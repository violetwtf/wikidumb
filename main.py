import discord
import json
import random
import requests

client: discord.Client = discord.Client()
alpha = 'abcdefghijklmnopqrstuvwxyz'
do_copypasta = False

api_url = 'https://en.wikipedia.org/w/api.php?format=json'

search_url = api_url + '&action=opensearch' \
             '&limit=1' \
             '&namespace=0' \
             '&redirects=resolve' \
             '&search='

read_url = api_url + '&action=query' \
                     '&prop=extracts' \
                     '&explaintext=1' \
                     '&exintro=1' \
                     '&titles='

wikitext_url = api_url + '&action=parse&prop=wikitext&page='


def main() -> None:
    """
    Application entrypoint
    """
    client.run(get_config()['token'])


@client.event
async def on_message(message: discord.Message):
    global do_copypasta

    if message.author.bot:
        return

    if random.randint(0, 4) > 0 and not do_copypasta:  # 20% chance
        return

    content = message.clean_content.lower()
    words = list(filter(word_filter, content.split(' ')))

    copypasta = get_wikipedia_copypasta(words)

    if not copypasta:
        do_copypasta = True  # Try on next message
    else:
        await message.channel.send(copypasta)


def get_wikipedia_copypasta(words: list, tries: int = 0):
    """
    Returns a Wikipedia copypasta for a given word list. Will try and pick a
    random word to get a copypasta for.

    :param words: Word list
    :param tries: Internal parameter - don't set!
    :return: A Wikipedia copypata, or None if none can be found
    """
    if tries == 5 or not words:
        return None

    word = random.choice(words)
    words.remove(word)

    article = get_article_for_query(word)
    word_clean = clean_word(word)
    article_clean = clean_word(article)

    if word_clean != article_clean:
        return get_wikipedia_copypasta(words, tries + 1)

    para = get_first_para_from_article(article)

    if 'may refer to' in para:
        next_article = get_first_link_in_article(article)
        para = get_first_para_from_article(next_article)

    return para


def get_first_para_from_article(article: str):
    print('get_first_para_from_article: ' + article)

    # Pages is a dict of page IDs to objects
    raw = requests.get(read_url + article).json()
    pages = raw['query']['pages']
    text = list(pages.items())[0][1]['extract']

    if 'may refer to' in text:
        return text

    return text.split('\n')[0]


def get_first_link_in_article(article: str):
    print('get_first_link_in_article: ' + article)

    raw = requests.get(wikitext_url + article).json()
    text = raw['parse']['wikitext']['*']
    link = text.split('[[')[1].split(']]')[0]

    return link


def get_article_for_query(query: str) -> str:
    print('get_article_for_query: ' + query)
    return requests.get(search_url + query).json()[1][0]


def clean_word(word: str) -> str:
    word = word.lower()
    out = ''

    for _, c in enumerate(word):
        if c in alpha:
            out += c

    return out


def word_filter(word: str) -> bool:
    """
    Filters words to make them more Wikipedia friendly
    :param word: Word to filter
    :return: OK
    """
    for _, c in enumerate(word):
        if c not in alpha:
            return False
    return True


def get_config() -> dict:
    """
    Loads config from disk
    :return: Config dict
    """
    with open('config.json', 'r') as file:
        config = json.load(file)
        return config


if __name__ == '__main__':
    main()