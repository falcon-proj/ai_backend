from common_imports import *

# Custom method to degenerate the text into key points and examples
# It uses OpenAI embeddings to embed the sentences
def embed_chunk(keypoints_with_examples, text):
    anchors = [ _.key_point + '. Example: '+ ' ,or, '.join(_.examples) for _ in keypoints_with_examples.key_points]
    anchor_embs = langchain_OpenAIEmbeddings().embed_documents(anchors)
    single_sentences_list = re.split(r'(?<=[.?!;])\s+', text)
    sentence_embs = langchain_OpenAIEmbeddings().embed_documents(single_sentences_list)

    # return anchors, anchor_embs, single_sentences_list, sentence_embs
    pointer_anch, pointer_sent = 0,0

    # Grouping sentence_embs wrt cosine similarity with anchor_embs
    # Iterate over the sentence_embs and find the cosine similarity with anchor_embs starting from pointer_anch
    # Now if the cosine similarity with next anchor is greater than the current anchor, then we move to the next anchor
    # and store the current sentence in the next group

    cross_corr = cosine_similarity(anchor_embs, sentence_embs)

    # Do row wise 3 window maxpooling operation on cross_corr
    max_pool_window = 3
    for i in range(len(cross_corr)):
        for j in range(len(cross_corr[i])):
            cross_corr[i][j] = cross_corr[i][j:j+max_pool_window].max()

    grouped_sentences = []

    while pointer_anch < len(anchors):        
        group = []
        while pointer_sent < len(single_sentences_list):
            if pointer_anch < len(anchor_embs)-1 and cross_corr[pointer_anch][pointer_sent] > cross_corr[pointer_anch+1][pointer_sent]:
                group.append(single_sentences_list[pointer_sent])
                pointer_sent += 1
            else:
                break
        
        if len(group) > 0 or (pointer_anch == len(anchor_embs)-1 and pointer_sent < len(single_sentences_list)):
            # print(">>>> Assigned")
            grouped_sentences.append({
                "key_point": anchors[pointer_anch],
                "sub_context": " ".join(group),
                "contains_rule_risk": keypoints_with_examples.key_points[pointer_anch].contains_rule_risk
            })
        pointer_anch += 1

    # assign the remaining sentences to the last group
    if pointer_sent < len(single_sentences_list):
        group = []
        while pointer_sent < len(single_sentences_list):
            group.append(single_sentences_list[pointer_sent])
            pointer_sent += 1
        grouped_sentences[-1]["sub_context"]+= " ".join(group)

      # Remove no risk or rule containing sentences
    mod_grouped_sentences = [ _ for _ in grouped_sentences if _.get("contains_rule_risk",False)]
    # Percentage of sentences removed
    print(f"Percentage of sentences removed : {100*(1-len(mod_grouped_sentences)/len(grouped_sentences))}%")

    return mod_grouped_sentences