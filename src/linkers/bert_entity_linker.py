import os
import torch
import logging

from typing import Optional, Dict, Tuple, List, Any
from os.path import isfile
from transformers import BertTokenizerFast
from math import floor

import spacy
from spacy.tokens import Doc
from spacy.vocab import Vocab
from spacy.kb import KnowledgeBase, Candidate

from src import settings
from src.settings import NER_IGNORE_TAGS
from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_prediction import EntityPrediction
from src.models.entity_database import EntityDatabase
from src.models.bert_model import BertClassifier
from src.ner.ner_postprocessing import NERPostprocessor
from src.utils.dates import is_date

logger = logging.getLogger("main." + __name__.split(".")[-1])


class BertEntityLinker(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.model = spacy.load(settings.LARGE_MODEL_NAME)

        # Get config variables
        self.linker_identifier = config["name"] if "name" in config else "BERTModel"
        self.ner_identifier = "EnhancedSpacy"
        model_path = config["model_path"] if "model_path" in config else None
        if model_path is None:
            raise KeyError("BERT entity linker config does not contain the required attribute \"model_path\".")
        if not os.path.exists(model_path):
            raise OSError("Path to the BERT entity linking model does not exist: %s" % model_path)

        if not self.model.has_pipe("ner_postprocessor"):
            ner_postprocessor = NERPostprocessor(entity_db)
            self.model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")

        wikipedia_abstracts_file = settings.QID_TO_ABSTRACTS_FILE
        self.wikipedia_abstracts = {}
        if not isfile(wikipedia_abstracts_file):
            raise FileNotFoundError(f"Can't find Wikipedia abstracts file at {wikipedia_abstracts_file}.")
        logger.info("Loading Wikipedia abstracts ...")
        for line in open(wikipedia_abstracts_file):
            values = line[:-1].split('\t')
            self.wikipedia_abstracts[values[0]] = (values[1], values[2].strip())

        logger.info("Loading knowledge base ...")
        vocab_path = settings.VOCAB_DIRECTORY
        kb_path = settings.KB_FILE
        vocab = Vocab().from_disk(vocab_path)
        self.kb = KnowledgeBase(vocab=vocab)
        self.kb.load_bulk(kb_path)

        logger.info("Loading tokenizer ...")
        self.tokenizer = BertTokenizerFast.from_pretrained(model_path, do_lower_case=True)

        logger.info("Loading trained BERT entity linker ...")
        self.linker_model = BertClassifier.from_pretrained(model_path)
        self.linker_model.eval()
        torch.set_grad_enabled(False)

        # Use Cuda if Cuda enabled GPU is available
        self.device = torch.device("cpu")
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
            logger.info('Using device:', torch.cuda.get_device_name(0))
        else:
            logger.info('Using CPU')

        self.linker_model.to(self.device)
        logger.info("Ready.")

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)
        predictions = {}

        for ent in doc.ents:
            if ent.label_ in NER_IGNORE_TAGS:
                continue
            # The token span of the mention
            token_span = (ent.start, ent.end)
            snippet = ent.text
            if uppercase and snippet.islower():
                continue
            if is_date(snippet):
                continue
            candidates = self.kb.get_candidates(snippet)
            if not candidates:
                continue

            input_ids, attention_mask, token_type_ids = self.get_model_input(token_span, candidates, doc)

            prediction = torch.empty([len(candidates), 1])

            i = 0
            batch_size = 32
            while i < len(candidates):
                pred = self.linker_model(input_ids=input_ids[i:i+batch_size],
                                         attention_mask=attention_mask[i:i+batch_size],
                                         token_type_ids=token_type_ids[i:i+batch_size])
                prediction[i:i+batch_size] = pred.cpu()
                i += batch_size

            prediction = prediction
            # Top prediction is highest number
            top_pred = prediction.max(0)
            top_pred_val = top_pred[0].item()
            top_pred_ind = top_pred[1].item()

            if top_pred_val > 0:
                entity_id = candidates[top_pred_ind].entity_
            else:
                continue

            candidates = {cand.entity_ for cand in candidates}
            # The char span of the mention
            span = (ent.start_char, ent.end_char)
            predictions[span] = EntityPrediction(span, entity_id, candidates)

        return predictions

    def get_model_input(self,
                        span: Tuple[int, int],
                        candidates: List[Candidate],
                        doc: Doc) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        all_input_ids = []
        all_attention_mask = []
        all_token_type_ids = []

        CLS_ID = self.tokenizer.convert_tokens_to_ids('[CLS]')
        SEP_ID = self.tokenizer.convert_tokens_to_ids('[SEP]')
        PAD_ID = self.tokenizer.convert_tokens_to_ids('[PAD]')

        max_len = self.linker_model.config.max_position_embeddings

        # Tokenize the document first
        doc_words = [t.text for t in doc]
        doc_tokenized = self.tokenizer.encode(
                doc_words,
                truncation=False,
                add_special_tokens=False,
                is_split_into_words=True,
                verbose=False
            )
        for candidate in candidates:
            cand_id = candidate.entity_
            # Max number of tokens for the abstract context.
            # Half of the total length, excluding two [SEP] and one [CLS] tokens
            max_cand_len = floor((max_len - 3) / 2)

            # Start with the candidate title
            cand_abstract = self.wikipedia_abstracts[cand_id][0]
            # Add a truncated part of the abstract (faster for very long abstracts)
            cand_abstract += ' ' + ' '.join(self.wikipedia_abstracts[cand_id][1].split(' ')[:int(max_cand_len*1.5)])
            # Tokenize with truncation
            cand_tokens = self.tokenizer.encode(
                                cand_abstract,
                                max_length=max_cand_len,
                                truncation=True,
                                add_special_tokens=False
                            )

            # The quota for the named entity context in number of tokens
            entity_text = doc[span[0]:span[1]].text
            ne_tokenized = self.tokenizer.encode(
                    entity_text,
                    add_special_tokens=False,
                    is_split_into_words=False
                )
            max_context_len = max_len - 3 - len(cand_tokens) - len(ne_tokenized)

            # Make sure we get at least some words after the token
            start = max(0, span[1] + 15 - max_context_len)
            end = start + max_context_len
            entity_tokens = ne_tokenized + doc_tokenized[start:end]

            input_ids = [CLS_ID] + entity_tokens + [SEP_ID] + cand_tokens + [SEP_ID]
            pad_len = max_len - len(input_ids)
            attention_mask = [1] * len(input_ids) + [0] * pad_len
            input_ids += [PAD_ID] * pad_len

            token_type_ids = [0] * (2 + len(entity_tokens)) + [1] * (1 + len(cand_tokens)) + [0] * pad_len
            all_input_ids.append(torch.Tensor(input_ids).unsqueeze(0).to(dtype=torch.long))
            all_attention_mask.append(torch.Tensor(attention_mask).unsqueeze(0).to(dtype=torch.long))
            all_token_type_ids.append(torch.Tensor(token_type_ids).unsqueeze(0).to(dtype=torch.long))

        all_input_ids = torch.cat(all_input_ids).to(self.device)
        all_attention_mask = torch.cat(all_attention_mask).to(self.device)
        all_token_type_ids = torch.cat(all_token_type_ids).to(self.device)
        return all_input_ids, all_attention_mask, all_token_type_ids

    def has_entity(self, entity_id: str) -> bool:
        return self.kb.contains_entity(entity_id)
