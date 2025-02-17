import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from dotenv import load_dotenv
import os
import pymysql

# Carregar variáveis do ambiente
load_dotenv()
TOKEN = os.getenv("TOKEN")

# IDs do Servidor e Canais
GUILD_ID = 1257646880188272723
CANAL_SOLICITACAO = 1333466528892321875
CANAL_ADMIN = 1257646928091549778
CARGO_MEMBRO_DISCORD = 1335470710746775632

# Configuração do Banco de Dados
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "vrpex"

def conectar_bd():
    return pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

# Criando o bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'\n[INFO] Bot {bot.user} está online e pronto para uso!')
    print("[INFO] Registrando views...")
    bot.add_view(WhitelistView())  # Garante que a view persista
    print("[INFO] Views registradas com sucesso!")

# Criando o formulário de whitelist
class WhitelistModal(Modal):
    def __init__(self):
        super().__init__(title="Liberando seu Acesso")
        self.nome = TextInput(label="Nome do seu personagem dentro do jogo", required=True)
        self.id_jogador = TextInput(label="Informe seu ID para realizar a whitelist", required=True)
        
        self.add_item(self.nome)
        self.add_item(self.id_jogador)

    async def on_submit(self, interaction: discord.Interaction):
        print(f'[DEBUG] Nova solicitação de WL de {interaction.user}')
        canal_admin = bot.get_channel(CANAL_ADMIN)
        if canal_admin:
            await canal_admin.send(
                f"**Nova solicitação de whitelist:**\n"
                f"**Nome:** {self.nome.value}\n"
                f"**ID:** {self.id_jogador.value}\n"
                f"**Usuário:** {interaction.user.mention}\n"
                f"Aprovar com: `!aprovar {self.id_jogador.value} @{interaction.user}`"
            )
            await interaction.response.send_message("Sua solicitação foi enviada para análise!", ephemeral=True)
        else:
            print('[ERRO] Canal de admin não encontrado!')
            await interaction.response.send_message("Erro: Canal de Admin não encontrado!", ephemeral=True)

# Criando o botão de whitelist
class WhitelistView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Evita expiração da View

    @discord.ui.button(label="Realizar Whitelist", style=discord.ButtonStyle.green, custom_id="whitelist_button")
    async def whitelist_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f'[DEBUG] Botão de whitelist pressionado por {interaction.user}')
        await interaction.response.send_modal(WhitelistModal())

# Comando para iniciar a solicitação de whitelist
@bot.command()
async def solicitar(ctx):
    print(f'[DEBUG] Comando !solicitar chamado por {ctx.author} no canal {ctx.channel.id}')
    view = WhitelistView()
    
    async for message in ctx.channel.history(limit=50):
        if message.author == bot.user and "Clique no botão abaixo para solicitar sua whitelist:" in message.content:
            await message.edit(content="Clique no botão abaixo para solicitar sua whitelist:", view=view)
            print("[DEBUG] Mensagem de whitelist atualizada.")
            return
    
    await ctx.send("Clique no botão abaixo para solicitar sua whitelist:", view=view)
    print("[DEBUG] Mensagem de whitelist enviada.")

# Comando para aprovar whitelist (somente administradores)
@bot.command()
@commands.has_permissions(administrator=True)
async def aprovar(ctx, id_jogador: int, membro: discord.Member):
    print(f'[DEBUG] Comando !aprovar chamado por {ctx.author} para {membro} (ID: {id_jogador})')
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        sql = "UPDATE vrp_users SET whitelisted = 1 WHERE id = %s"
        cursor.execute(sql, (id_jogador,))
        conn.commit()
        conn.close()
        
        cargo_discord = ctx.guild.get_role(CARGO_MEMBRO_DISCORD)
        await membro.add_roles(cargo_discord)
        await ctx.send(f"Whitelist aprovada para {membro.mention} (ID: {id_jogador}). Cargo de membro no Discord atribuído!")
    except Exception as e:
        print(f'[ERRO] Falha ao aprovar whitelist: {e}')
        await ctx.send(f"Erro ao aprovar whitelist: {e}")

bot.run(TOKEN)
