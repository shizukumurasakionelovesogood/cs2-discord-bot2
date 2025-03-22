import disnake
from disnake.ext import commands

class TextAdventureGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rooms = {
            'start': {
                'description': 'Вы находитесь в темной комнате. На севере есть дверь.',
                'exits': {'north': 'hallway'}
            },
            'hallway': {
                'description': 'Вы находитесь в длинном коридоре. На юге и востоке есть двери.',
                'exits': {'south': 'start', 'east': 'treasure_room'}
            },
            'treasure_room': {
                'description': 'Вы нашли комнату с сокровищами! Здесь есть сундук с сокровищами.',
                'exits': {'west': 'hallway'}
            }
        }
        self.current_room = 'start'

    @commands.slash_command(name="adventure", description="Начать текстовое приключение", guild_ids=[994523162148601886])
    async def adventure(self, inter):
        await inter.response.send_message(self.rooms[self.current_room]['description'])

    @commands.slash_command(name="go", description="Перейти в другую комнату", guild_ids=[994523162148601886])
    async def go(self, inter, direction: str):
        if direction in self.rooms[self.current_room]['exits']:
            self.current_room = self.rooms[self.current_room]['exits'][direction]
            await inter.response.send_message(self.rooms[self.current_room]['description'])
        else:
            await inter.response.send_message("Вы не можете пойти туда.")

    @commands.slash_command(name="new_game", description="Начать новую игру", guild_ids=[994523162148601886])
    async def new_game(self, inter):
        self.current_room = 'start'
        await inter.response.send_message("Новая игра началась. Вы находитесь в темной комнате. На севере есть дверь.")

def setup(bot):
    bot.add_cog(TextAdventureGame(bot))
