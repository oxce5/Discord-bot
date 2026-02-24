import discord
from discord.ext import commands
from discord.ui import View, Button

class HelpView(View):
    """View with Previous/Next buttons for help pagination"""
    
    def __init__(self, bot, categories, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.categories = categories
        self.current_page = 0
        self.author = None
    
    async def on_timeout(self):
        """Disable buttons when view times out"""
        for item in self.children:
            item.disabled = True
        # Note: We can't edit the message here without the original message reference
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the command author to use the buttons"""
        if self.author and interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This help menu is not for you!", ephemeral=True)
            return False
        return True
    
    def create_embed(self, page_index: int) -> discord.Embed:
        """Create embed for a specific page"""
        category_name, commands_list = self.categories[page_index]
        
        embed = discord.Embed(
            title=f"Help - {category_name}",
            description=f"Page {page_index + 1} of {len(self.categories)}",
            color=discord.Color.blue()
        )
        
        for cmd_name, cmd_description in commands_list:
            # Most commands use the bot prefix (e.g. !ping). Some entries are prefixless (e.g. ai <prompt>).
            if cmd_name.lower().startswith("ai"):
                display_name = f"`{cmd_name}`"
            else:
                display_name = f"`!{cmd_name}`"
            embed.add_field(
                name=display_name,
                value=cmd_description,
                inline=False
            )
        
        embed.set_footer(text=f"Use !help to see all commands")
        return embed
    
    def update_buttons(self):
        """Update button states based on current page"""
        # Previous button
        self.children[0].disabled = self.current_page == 0
        
        # Next button
        self.children[1].disabled = self.current_page == len(self.categories) - 1
    
    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.primary, row=0)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = self.create_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary, row=0)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.categories) - 1:
            self.current_page += 1
            self.update_buttons()
            embed = self.create_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)

class HelpCommand(commands.Cog):
    """Custom help command with categories"""
    
    def __init__(self, bot):
        self.bot = bot
        # Remove default help command if it exists
        if self.bot.get_command('help'):
            self.bot.remove_command('help')
    
    def get_command_categories(self):
        """Organize commands into categories"""
        categories = {
            "Basic Commands": [],
            "AI": [],
            "Role Management": [],
            "Webhook Management": []
        }
        
        # Get all commands (including from cogs)
        for command in self.bot.walk_commands():
            if isinstance(command, commands.Command) and not command.hidden:
                cmd_name = command.name
                cmd_description = command.description or command.brief or "No description available"
                
                # Build command info with aliases
                alias_text = ""
                if command.aliases:
                    alias_text = f" *(aliases: {', '.join([f'!{a}' for a in command.aliases])})*"
                
                # Categorize commands
                if cmd_name in ['hello', 'ping', 'poll', 'info']:
                    categories["Basic Commands"].append((cmd_name, cmd_description + alias_text))
                elif cmd_name in ['assignrole', 'removerole', 'listroles', 'createrole', 'deleterole']:
                    categories["Role Management"].append((cmd_name, cmd_description + alias_text))
                elif cmd_name in ['createwebhook', 'listwebhooks', 'deletewebhook', 'sendwebhook', 'webhookembed']:
                    categories["Webhook Management"].append((cmd_name, cmd_description + alias_text))
        
        # Sort commands within each category
        for category in categories:
            categories[category].sort(key=lambda x: x[0])

        # Add prefixless AI entry (not a discord.py Command)
        categories["AI"].append((
            "ai <prompt>",
            "Chat with the AI (no prefix). Example: `ai hi`"
        ))
        
        # Filter out empty categories and return as list
        return [(cat, cmds) for cat, cmds in categories.items() if cmds]
    
    @commands.command(name="help")
    @commands.has_permissions(view_channel=True, send_messages=True, embed_links=True)
    async def help_command(self, ctx):
        """Show help menu with categorized commands"""
        categories = self.get_command_categories()
        
        if not categories:
            await ctx.send("❌ No commands available.")
            return
        
        # Create view with buttons
        view = HelpView(self.bot, categories)
        view.author = ctx.author
        view.update_buttons()
        
        # Create initial embed (first page)
        embed = view.create_embed(0)
        
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
