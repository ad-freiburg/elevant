import os
import sys
import pprint
import numpy as np
import tensorflow as tf
import json
import copy

from readers.inference_reader import InferenceReader
from models.figer_model.el_model import ELModel
from readers.config import Config
from readers.vocabloader import VocabLoader

np.set_printoptions(threshold=np.inf)
np.set_printoptions(precision=7)

pp = pprint.PrettyPrinter()

flags = tf.app.flags
flags.DEFINE_integer("max_steps", 32000, "Maximum of iteration [450000]")
flags.DEFINE_integer("pretraining_steps", 32000, "Number of steps to run pretraining")
flags.DEFINE_float("learning_rate", 0.005, "Learning rate of adam optimizer [0.001]")
flags.DEFINE_string("model_path", "", "Path to trained model")
flags.DEFINE_string("dataset", "el-figer", "The name of dataset [ptb]")
flags.DEFINE_string("checkpoint_dir", "/tmp",
                    "Directory name to save the checkpoints [checkpoints]")
flags.DEFINE_integer("batch_size", 1, "Batch Size for training and testing")
flags.DEFINE_integer("word_embed_dim", 300, "Word Embedding Size")
flags.DEFINE_integer("context_encoded_dim", 100, "Context Encoded Dim")
flags.DEFINE_integer("context_encoder_num_layers", 1, "Num of Layers in context encoder network")
flags.DEFINE_integer("context_encoder_lstmsize", 100, "Size of context encoder hidden layer")
flags.DEFINE_integer("coherence_numlayers", 1, "Number of layers in the Coherence FF")
flags.DEFINE_integer("jointff_numlayers", 1, "Number of layers in the Coherence FF")
flags.DEFINE_integer("num_cand_entities", 30, "Num CrossWikis entity candidates")
flags.DEFINE_float("reg_constant", 0.00, "Regularization constant for NN weight regularization")
flags.DEFINE_float("dropout_keep_prob", 0.6, "Dropout Keep Probability")
flags.DEFINE_float("wordDropoutKeep", 0.6, "Word Dropout Keep Probability")
flags.DEFINE_float("cohDropoutKeep", 0.4, "Coherence Dropout Keep Probability")
flags.DEFINE_boolean("decoder_bool", True, "Decoder bool")
flags.DEFINE_boolean("strict_context", False, "Strict Context exludes mention surface")
flags.DEFINE_boolean("pretrain_wordembed", True, "Use Word2Vec Embeddings")
flags.DEFINE_boolean("coherence", True, "Use Coherence")
flags.DEFINE_boolean("typing", True, "Perform joint typing")
flags.DEFINE_boolean("el", True, "Perform joint typing")
flags.DEFINE_boolean("textcontext", True, "Use text context from LSTM")
flags.DEFINE_boolean("useCNN", False, "Use wiki descp. CNN")
flags.DEFINE_boolean("glove", True, "Use Glove Embeddings")
flags.DEFINE_boolean("entyping", False, "Use Entity Type Prediction")
flags.DEFINE_integer("WDLength", 100, "Length of wiki description")
flags.DEFINE_integer("Fsize", 5, "For CNN filter size")

flags.DEFINE_string("optimizer", 'adam', "Optimizer to use. adagrad, adadelta or adam")

flags.DEFINE_string("config", 'configs/config.ini',
                    "VocabConfig Filepath")
flags.DEFINE_string("test_out_fp", "", "Write Test Prediction Data")

flags.DEFINE_string("out_file", "", "Write inference data to the specified file")
flags.DEFINE_string("in_file", "", "Input file to be linked. With one document in a single line")
flags.DEFINE_string("contains_ner", False, "Input comes with recognized mentions so don't perform NER.")
flags.DEFINE_string("spacy", False, "Use spacy document preprocessing instead of ccg_nlpy.")

FLAGS = flags.FLAGS


def FLAGS_check(FLAGS):
    if not (FLAGS.textcontext and FLAGS.coherence):
        print("*** Local and Document context required ***")
        sys.exit(0)
    assert os.path.exists(FLAGS.model_path), "Model path doesn't exist."


def main(_):
    pp.pprint(flags.FLAGS.__flags)

    FLAGS_check(FLAGS)

    config = Config(FLAGS.config, verbose=False)
    vocabloader = VocabLoader(config)

    FLAGS.dropout_keep_prob = 1.0
    FLAGS.wordDropoutKeep = 1.0
    FLAGS.cohDropoutKeep = 1.0

    reader = InferenceReader(config=config,
                             vocabloader=vocabloader,
                             num_cands=FLAGS.num_cand_entities,
                             batch_size=FLAGS.batch_size,
                             strict_context=FLAGS.strict_context,
                             pretrain_wordembed=FLAGS.pretrain_wordembed,
                             coherence=FLAGS.coherence,
                             spacy_doc_processing=FLAGS.spacy)
    model_mode = 'inference'

    if FLAGS.out_file:
        out_file = open(FLAGS.out_file, "w", encoding="utf8")

    with open(FLAGS.in_file, 'r', encoding="utf8") as f:
        for line_num, line in enumerate(f):
            print("*" * 80)
            print("Processing doc %d" % line_num)
            # NER yields wrong results if line ends on an entity (without trailing punctuation).
            # As a hack, append a dot if line ends on alphanumeric. This should not change the results.
            line = line.strip()
            if line and (line[-1].isalnum() or line[-1] == "]"):
                print("Add punctuation to end of line.")
                line += " ."
            reader.initialize_for_doc(line, FLAGS.contains_ner)
            if not FLAGS.spacy:
                docta = reader.ccgdoc
            if len(reader.ner_cons_list) > 0:
                with tf.Graph().as_default():
                    config_proto = tf.ConfigProto()
                    config_proto.allow_soft_placement = True
                    config_proto.gpu_options.allow_growth = True
                    sess = tf.Session(config=config_proto)
                    with sess.as_default():
                        model = ELModel(
                            sess=sess, reader=reader, dataset=FLAGS.dataset,
                            max_steps=FLAGS.max_steps,
                            pretrain_max_steps=FLAGS.pretraining_steps,
                            word_embed_dim=FLAGS.word_embed_dim,
                            context_encoded_dim=FLAGS.context_encoded_dim,
                            context_encoder_num_layers=FLAGS.context_encoder_num_layers,
                            context_encoder_lstmsize=FLAGS.context_encoder_lstmsize,
                            coherence_numlayers=FLAGS.coherence_numlayers,
                            jointff_numlayers=FLAGS.jointff_numlayers,
                            learning_rate=FLAGS.learning_rate,
                            dropout_keep_prob=FLAGS.dropout_keep_prob,
                            reg_constant=FLAGS.reg_constant,
                            checkpoint_dir=FLAGS.checkpoint_dir,
                            optimizer=FLAGS.optimizer,
                            mode=model_mode,
                            strict=FLAGS.strict_context,
                            pretrain_word_embed=FLAGS.pretrain_wordembed,
                            typing=FLAGS.typing,
                            el=FLAGS.el,
                            coherence=FLAGS.coherence,
                            textcontext=FLAGS.textcontext,
                            useCNN=FLAGS.useCNN,
                            WDLength=FLAGS.WDLength,
                            Fsize=FLAGS.Fsize,
                            entyping=FLAGS.entyping)

                        (predTypScNPmat_list,
                         widIdxs_list,
                         priorProbs_list,
                         textProbs_list,
                         jointProbs_list,
                         evWTs_list,
                         pred_TypeSetsList) = model.inference(ckptpath=FLAGS.model_path)

                        numMentionsInference = len(widIdxs_list)
                        numMentionsReader = 0
                        for sent_idx in reader.sentidx2ners:
                            numMentionsReader += len(reader.sentidx2ners[sent_idx])
                        assert numMentionsInference == numMentionsReader

                        mentionnum = 0
                        entityTitleList = []
                        sentenceList = []
                        for sent_idx in reader.sentidx2ners:
                            nerDicts = reader.sentidx2ners[sent_idx]
                            sentence = ' '.join(reader.sentences_tokenized[sent_idx])
                            for s, ner in nerDicts:
                                [evWTs, evWIDS, evProbs] = evWTs_list[mentionnum]
                                predTypes = pred_TypeSetsList[mentionnum]
                                print(reader.bracketMentionInSentence(sentence, ner))
                                print("Prior: {} {}, Context: {} {}, Joint: {} {}".format(
                                    evWTs[0], evProbs[0], evWTs[1], evProbs[1],
                                    evWTs[2], evProbs[2]))

                                entityTitleList.append(evWTs[2])
                                sentenceList.append(sent_idx)
                                print("Predicted Entity Types : {}".format(predTypes))
                                print("\n")
                                mentionnum += 1
                        if FLAGS.spacy:
                            cons_list = reader.ner_cons_list

                            # Compute the character start and end offset for each mention
                            for i, cons in enumerate(cons_list):
                                if i > len(entityTitleList):
                                    print("Length discrepancy")
                                    print(entityTitleList, cons_list)
                                cons['entity_reference'] = entityTitleList[i]
                                cons['start_char'] = reader.ner_offsets[i][0]
                                cons['end_char'] = reader.ner_offsets[i][1]
                            if len(cons_list) != len(reader.ner_offsets):
                                print("LIST LENGTHS DIFFER!!!", "*"*80)

                            predictions = {"predictions": cons_list}
                        else:
                            elview = copy.deepcopy(docta.view_dictionary['NER_CONLL'])
                            elview.view_name = 'ENG_NEURAL_EL'

                            # Compute the character start and end offset for each mention
                            token_offsets = docta.as_json['tokenOffsets']
                            sentence_end_positions = docta.as_json['sentences']['sentenceEndPositions']
                            for i, cons in enumerate(elview.cons_list):
                                cons['entity_reference'] = entityTitleList[i]
                                sentence_idx = sentenceList[i]
                                sentence_start_token_idx = sentence_end_positions[
                                    sentence_idx - 1] if sentence_idx > 0 else 0
                                start_token_idx = sentence_start_token_idx + cons['start']
                                start_char = token_offsets[start_token_idx]['startCharOffset']
                                end_token_idx = sentence_start_token_idx + cons['end']
                                end_char = token_offsets[end_token_idx]['endCharOffset']
                                cons['start_char'] = start_char
                                cons['end_char'] = end_char

                            docta.view_dictionary['ENG_NEURAL_EL'] = elview
                            predictions = {"predictions": elview.cons_list}

                        if FLAGS.out_file:
                            out_file.write(json.dumps(predictions) + "\n")
                        else:
                            print(json.dumps(predictions))
                        del model
                tf.reset_default_graph()
            else:
                # NER module didn't produce any mentions
                out_file.write('{"predictions": []}\n')

    if FLAGS.out_file:
        out_file.close()
    sys.exit()


if __name__ == '__main__':
    tf.app.run()
