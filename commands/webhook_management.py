import discord
from discord.ext import commands
from discord import Webhook

class WebhookManagement(commands.Cog):
    """Webhook management commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="createwebhook", aliases=["cw", "webhook"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_webhooks=True
    )
    async def create_webhook(self, ctx, channel: discord.TextChannel = None, *, name: str = None):
        """Create a webhook in a channel"""
        target_channel = channel or ctx.channel
        
        if not name:
            name = f"Webhook-{ctx.author.name}"
        
        try:
            webhook = await target_channel.create_webhook(name=name)
            embed = discord.Embed(
                title="✅ Webhook Created",
                description=f"Webhook '{name}' created in {target_channel.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="Webhook URL", value=f"`{webhook.url}`", inline=False)
            embed.add_field(name="Webhook ID", value=webhook.id, inline=True)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create webhooks.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name="listwebhooks", aliases=["lw", "webhooks"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        read_message_history=True,
        manage_webhooks=True
    )
    async def list_webhooks(self, ctx, channel: discord.TextChannel = None):
        """List all webhooks in a channel or server"""
        target_channel = channel
        
        if target_channel:
            webhooks = await target_channel.webhooks()
        else:
            # Get all webhooks in the server
            webhooks = []
            for ch in ctx.guild.text_channels:
                try:
                    ch_webhooks = await ch.webhooks()
                    webhooks.extend(ch_webhooks)
                except:
                    pass
        
        if not webhooks:
            await ctx.send("❌ No webhooks found.")
            return
        
        embed = discord.Embed(
            title=f"Webhooks ({len(webhooks)})",
            color=discord.Color.blue()
        )
        
        webhook_list = []
        for webhook in webhooks[:10]:  # Limit to 10
            channel_mention = f"<#{webhook.channel_id}>" if webhook.channel_id else "Unknown"
            webhook_list.append(f"**{webhook.name}** - {channel_mention}")
        
        embed.description = "\n".join(webhook_list) if webhook_list else "No webhooks"
        if len(webhooks) > 10:
            embed.set_footer(text=f"Showing first 10 of {len(webhooks)} webhooks")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="deletewebhook", aliases=["dw", "removewebhook"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_webhooks=True
    )
    async def delete_webhook(self, ctx, webhook_id: int = None, *, webhook_name: str = None):
        """Delete a webhook by ID or name"""
        if not webhook_id and not webhook_name:
            await ctx.send("❌ Please provide either a webhook ID or name.")
            return
        
        # Find the webhook
        webhook = None
        if webhook_id:
            try:
                webhook = await self.bot.fetch_webhook(webhook_id)
            except discord.NotFound:
                await ctx.send("❌ Webhook not found.")
                return
        else:
            # Search by name
            for channel in ctx.guild.text_channels:
                try:
                    webhooks = await channel.webhooks()
                    webhook = discord.utils.get(webhooks, name=webhook_name)
                    if webhook:
                        break
                except:
                    pass
        
        if not webhook:
            await ctx.send("❌ Webhook not found.")
            return
        
        try:
            webhook_name = webhook.name
            await webhook.delete()
            embed = discord.Embed(
                title="✅ Webhook Deleted",
                description=f"Webhook '{webhook_name}' has been deleted.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete this webhook.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name="sendwebhook", aliases=["sw", "webhooksend"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_webhooks=True
    )
    async def send_webhook(self, ctx, webhook_id: int, *, message: str):
        """Send a message through a webhook"""
        try:
            webhook = await self.bot.fetch_webhook(webhook_id)
            
            await webhook.send(
                content=message,
                username=ctx.author.display_name,
                avatar_url=ctx.author.display_avatar.url
            )
            
            embed = discord.Embed(
                title="✅ Message Sent",
                description=f"Message sent via webhook '{webhook.name}'",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("❌ Webhook not found.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to use this webhook.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name="webhookembed", aliases=["we"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_webhooks=True
    )
    async def send_webhook_embed(self, ctx, webhook_id: int, *, title: str):
        """Send an embed through a webhook"""
        try:
            webhook = await self.bot.fetch_webhook(webhook_id)
            
            embed = discord.Embed(
                title=title,
                description="This is a webhook embed message",
                color=discord.Color.blue()
            )
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            
            await webhook.send(
                embed=embed,
                username=ctx.author.display_name,
                avatar_url=ctx.author.display_avatar.url
            )
            
            await ctx.send("✅ Embed sent via webhook!")
        except discord.NotFound:
            await ctx.send("❌ Webhook not found.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to use this webhook.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @create_webhook.error
    @list_webhooks.error
    @delete_webhook.error
    @send_webhook.error
    @send_webhook_embed.error
    async def webhook_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            await ctx.send(f"❌ Missing required permissions: {', '.join(missing_perms)}")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Please provide all required arguments. Use `!help` for command usage.")

async def setup(bot):
    await bot.add_cog(WebhookManagement(bot))

