import argparse
import glob
import json
import os
import time
import re


def remove_hyperlinks(text):
    return re.sub(r"\[\[.*?\|(.*?)\]\]", r"\1", text)


def remove_annotation(text):
    return re.sub(r"\[\[[^\[]*?\|(.*?)\|[^\]]*?\]\]", r"\1", text)


def strip_entity_originals(text):
    return re.sub(r"(\[\[.*?\|.*?)\s+(\|.*?\]\])", r"\1\2", text)


def process_file(linked_article, original_article, output_filename, verbose=False):
    """
    Go through the final article character by character and compare it to the original article.
    Make sure they are the same except for entity annotations and hyperlinks.
    """
    out_file = open(output_filename, "w", encoding="utf8")
    # Get plain original text without hyperlinks
    original_lines_with_links = open(original_article, "r", encoding="utf8").readlines()
    original_lines = []
    for line in original_lines_with_links:
        if line.startswith("ACTUAL ENTITIES"):
            break
        line = remove_hyperlinks(line)
        original_lines.append(line)
    original_text = ''.join(original_lines).strip("\n") + "\n"

    linked_text = ''.join(open(linked_article, "r", encoding="utf8").readlines()).replace("\n", "")
    linked_text = strip_entity_originals(linked_text)

    i = 0
    o_i = 0
    new_text = ""
    in_entity = False
    section_count = 0
    while i < len(linked_text) and o_i < len(original_text):
        char = linked_text[i]
        original_char = original_text[o_i]
        if in_entity:
            if char == "|":
                section_count += 1
                new_text += char
                i += 1
            elif char == "]" and len(linked_text) > i+1 and linked_text[i+1] == "]":
                if section_count != 2:
                    print("SOMETHING WENT WRONG! Sentence: %s. Article: %s" % (linked_text, linked_article))
                new_text += "]]"
                i += 2
                in_entity = False
                section_count = 0
            elif section_count == 1:
                if original_char == char:
                    i += 1
                o_i += 1
                new_text += original_char
            else:
                i += 1
                new_text += char
        else:
            if char != original_char:
                if char == "[" and len(linked_text) > i+1 and linked_text[i+1] == "[" and not original_char.isspace():
                    i += 2
                    in_entity = True
                    new_text += "[["
                else:
                    o_i += 1
                    new_text += original_char
            else:
                new_text += original_char
                o_i += 1
                i += 1

    # Add remaining characters from the original text
    if o_i < len(original_text):
        original_char = original_text[o_i]
        new_text += original_char
        o_i += 1

    plain_new_text = remove_annotation(new_text)
    if verbose:
        print("*" * 80)
        print("Linked text:\n'%s" % linked_text)
        print("*" * 80)
        print("New text:\n'%s'" % new_text)
        print("*" * 80)
        print("Original text:\n'%s'" % original_text)
        print("*" * 80)
        print("Plain new text:\n'%s'" % plain_new_text)
        print("*" * 80)
        print()

    if plain_new_text != original_text:
        print(("*" * 10 + "Conversion failed for article %s" + "*" * 10) % linked_article)

    out_file.write(new_text)


def process(linked_article, original_article, file_directory):
    output_filename = file_directory + linked_article.split('/')[-1]
    process_file(linked_article, original_article, output_filename, verbose=False)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("--only_new", action="store_true",
                        help="Process only articles in the article directory \"new\".")

    args = parser.parse_args()

    config = json.load(open('config/config.json'))

    outputpath = config['outputpath']
    original_articlepath = outputpath + 'fixed_link_articles_benchmark/'
    final_articlepath = outputpath + 'almost_final_articles_benchmark/'
    benchmark_articlepath = outputpath + 'final_articles_benchmark/'

    if not os.path.isdir(benchmark_articlepath):
        try:
            mode = 0o755
            os.mkdir(benchmark_articlepath, mode)
        except FileNotFoundError:
            print('Not found: ' + benchmark_articlepath)
            exit(1)

    article_directories = glob.glob(final_articlepath + "*/")

    print("Processing articles at %s with information from %s" % (final_articlepath, original_articlepath))
    diff_acc = 0.0
    c = 0
    for article_directory in article_directories:
        folder_name = article_directory.split('/')[-2]

        if args.only_new and folder_name != "new":
            continue

        articles = glob.glob(article_directory + "*.txt")

        file_directory = benchmark_articlepath + folder_name + '/'

        if not os.path.isdir(file_directory):
            try:
                mode = 0o755
                os.mkdir(file_directory, mode)
            except FileNotFoundError:
                print('Not found: ' + file_directory)
                exit(1)

        start = time.time()

        for linked_article in articles:
            original_article = original_articlepath + folder_name + "/" + linked_article.split("/")[-1]
            process(linked_article, original_article, file_directory)

        end = time.time()
        diff_acc += end - start
        c += len(articles)
        avg = (diff_acc / c) * 1000
        print(str(c) + ', avg t: ' + str(avg), end='\r')
    print("Wrote final articles to %s" % benchmark_articlepath)


if __name__ == "__main__":
    main()
