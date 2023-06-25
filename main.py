import os
import random
import discord
import requests
from emoji import emojize
from dotenv import load_dotenv
from webserver import keep_alive

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
challenge = None
tags = [
  'implementation', 'math', 'greedy', 'dp', 'brute force',
  'constructive algorithms', 'sortings', 'binary search', 'strings',
  'combinatorics', 'two pointers', 'number theory'
]
ignored = []


class Challenge():

  def __init__(self, points):
    self.questions = [chr(65 + i) for i in range(0, int(points[0]))]
    self.points = [int(i) for i in points[1:]]
    self.solved = []
    self.leaderboard = dict()

  async def solve_question(self, question: str, author_id: str):
    question = question.upper()

    if question not in self.questions:
      raise Exception(f"Incorrect question id <@{author_id}>")
    if question in self.solved:
      raise Exception(f"Question is already solved <@{author_id}>")

    if author_id not in ignored:
      self.solved.append(question)
    self.leaderboard[author_id] = self.leaderboard.get(
      author_id, 0) + self.points[ord(question) - 65]


def fetchQuestions(question_count, question_desc):
  idx = 0
  question_url = []

  for i in range(question_count):
    resp = requests.get(
      f'https://codeforces.com/api/problemset.problems?tags={random.choice(tags)}'
    )
    data = resp.json()
    data = data['result']['problems']
    data = list(
      filter(lambda obj: obj.get('rating') == int(question_desc[idx]), data))
    data = random.choice(data)

    question_url.append(
      f"https://codeforces.com/problemset/problem/{data.get('contestId')}/{data.get('index')}"
    )
    idx += 2

  return question_url


@client.event
async def on_ready():
  print('Lockout bot is running!')


@client.event
async def on_message(message):
  global challenge
  if message.author == client.user:
    return

  # if message.content.startswith('$hello'):
  #     await message.channel.send(f'Hello <@{message.author.id}>')

  if message.content.startswith('>ignore'):
    if message.author.id in ignored:
      ignored.remove(message.author.id)
      await message.channel.send("Author is now not ignored")
    else:
      ignored.append(message.author.id)
      await message.channel.send("Author is now ignored")

  if message.content.startswith('>start challenge'):
    if challenge:
      await message.channel.send(
        f"Challenge already in progress <@{message.author.id}>")
      return

    await message.channel.send(f'Enter number of questions')
    question_count = await client.wait_for('message')

    await message.channel.send(
      f'Enter {question_count.content}, question rating and points')
    question_desc = await client.wait_for('message')
    question_desc = question_desc.content.split(' ')

    points = [question_count.content]
    for i in range(1, len(question_desc), 2):
      points.append(int(question_desc[i]))

    challenge = Challenge(points)
    question_url = fetchQuestions(int(question_count.content), question_desc)

    embed = discord.Embed(title="Questions")
    for i in range(len(question_url)):
      embed.add_field(name=f"{chr(65 + i)})    {question_url[i]}",
                      value="",
                      inline=False)

    await message.channel.send("Challenge started! @everyone", embed=embed)

  if message.content.startswith('>end challenge'):
    if not challenge:
      await message.channel.send('Challenge has not yet started')
      return

    leaderboard = challenge.leaderboard
    leaderboard = dict(
      sorted(leaderboard.items(), key=lambda item: item[1], reverse=True))
    embed = discord.Embed(title=f"Leaderboard {emojize(':sports_medal:')}")
    rank = 1

    for k, v in leaderboard.items():
      username = await client.fetch_user(k)
      score = v

      embed.add_field(name=f"{rank}) {username}    {score}",
                      value="",
                      inline=False)
      rank += 1

    await message.channel.send("Challenge completed! @everyone", embed=embed)
    challenge = None

  if message.content.endswith('done') and message.content.startswith('>'):
    if not challenge:
      await message.channel.send('Challenge has not yet started')
      return

    try:
      await challenge.solve_question(message.content[1], message.author.id)
    except Exception as e:
      await message.channel.send(str(e))
      return

    leaderboard = challenge.leaderboard
    leaderboard = dict(
      sorted(leaderboard.items(), key=lambda item: item[1], reverse=True))
    embed = discord.Embed(title=f"Leaderboard {emojize(':sports_medal:')}")
    rank = 1

    for k, v in leaderboard.items():
      username = await client.fetch_user(k)
      score = v

      embed.add_field(name=f"{rank}) {username}    {score}",
                      value="",
                      inline=False)
      rank += 1

    await message.channel.send("@everyone", embed=embed)

    if len(challenge.questions) == len(challenge.solved):
      await message.channel.send("Challenge completed! @everyone")
      challenge = None


keep_alive()
client.run(os.environ['BOT_TOKEN'])
