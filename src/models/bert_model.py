import torch
from torch import nn
from transformers import BertPreTrainedModel, BertModel


class BertClassifier(BertPreTrainedModel):
    def __init__(self, config):
        """
        :param config: a transformers Config object
        :param use_cls: whether to use the CLS token for classification,
                        or the hidden state of the last layer.
        """
        self.num_labels = 1
        super().__init__(config, num_labels=self.num_labels)

        # The BertClassifier with pooling layer depending on the use_cls parameter
        self.bert = BertModel(config, add_pooling_layer=False)

        # Classifier depends on if we use the pooled output (CLS) or the sequence output.
        cls_layers = []
        # Input dimension depending on number of tokens encodings
        input_dim = config.hidden_size * 3
        cls_layers.append(nn.Linear(input_dim, config.hidden_size))
        cls_layers.append(nn.GELU())
        cls_layers.append(nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps))
        cls_layers.append(nn.Linear(config.hidden_size, self.num_labels))
        # The classifier:
        self.classifier = nn.Sequential(*cls_layers)

        # Used in BCEWithLogitsLoss function to counteract unbalanced training sets
        self.class_weights = torch.ones([1])

        self.init_weights()

    def forward(
            self,
            input_ids=None,
            attention_mask=None,
            token_type_ids=None,
            position_ids=None,
            head_mask=None,
            inputs_embeds=None,
            labels=None,
            output_attentions=None,
            output_hidden_states=None):

        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=False
        )

        bert_output = outputs[0]

        # Position of the first token of the candidate (right after the [SEP] token)
        cand_pos = torch.argmax(token_type_ids, dim=1)

        # Get the embedding of the first token of the candidate over the batch
        cand_tensors = torch.cat(
            [t[i] for t, i in zip(bert_output, cand_pos)]
        ).reshape((bert_output.size(0), bert_output.size(-1)))

        # Flattened input of 3 * hidden_size features
        bert_output = torch.cat([bert_output[:, 0],
                                 bert_output[:, 1],
                                 cand_tensors], dim=1)

        # bert_output = self.dropout(bert_output)
        logits = self.classifier(bert_output)

        return logits
