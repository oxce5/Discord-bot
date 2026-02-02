import discord
from discord.ext import commands

class RoleManagement(commands.Cog):
    """Role management commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="assignrole", aliases=["ar", "giverole"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_roles=True
    )
    async def assign_role(self, ctx, member: discord.Member, *, role_name: str):
        """Assign a role to a member"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            await ctx.send(f"❌ Role '{role_name}' not found.")
            return
        
        # Check if bot can manage this role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send("❌ I don't have permission to assign this role (it's higher than my highest role).")
            return
        
        # Check if member already has the role
        if role in member.roles:
            await ctx.send(f"❌ {member.mention} already has the role {role.mention}.")
            return
        
        try:
            await member.add_roles(role)
            embed = discord.Embed(
                title="✅ Role Assigned",
                description=f"{member.mention} has been assigned the role {role.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to assign roles.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name="removerole", aliases=["rr", "takerole"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_roles=True
    )
    async def remove_role(self, ctx, member: discord.Member, *, role_name: str):
        """Remove a role from a member"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            await ctx.send(f"❌ Role '{role_name}' not found.")
            return
        
        # Check if bot can manage this role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send("❌ I don't have permission to remove this role (it's higher than my highest role).")
            return
        
        # Check if member has the role
        if role not in member.roles:
            await ctx.send(f"❌ {member.mention} doesn't have the role {role.mention}.")
            return
        
        try:
            await member.remove_roles(role)
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"{role.mention} has been removed from {member.mention}",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove roles.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name="listroles", aliases=["lr", "roles"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        read_message_history=True
    )
    async def list_roles(self, ctx, member: discord.Member = None):
        """List roles for a member or all server roles"""
        if member:
            # List member's roles
            roles = [role.mention for role in member.roles if role.name != "@everyone"]
            if not roles:
                await ctx.send(f"{member.mention} has no roles.")
                return
            
            embed = discord.Embed(
                title=f"Roles for {member.display_name}",
                description="\n".join(roles) if roles else "No roles",
                color=discord.Color.blue()
            )
            embed.add_field(name="Total Roles", value=len(roles), inline=True)
            await ctx.send(embed=embed)
        else:
            # List all server roles
            roles = [role.mention for role in ctx.guild.roles if role.name != "@everyone"]
            roles.reverse()  # Show highest roles first
            
            embed = discord.Embed(
                title=f"Server Roles ({len(roles)})",
                description="\n".join(roles[:20]) if len(roles) > 0 else "No roles",
                color=discord.Color.blue()
            )
            if len(roles) > 20:
                embed.set_footer(text=f"Showing first 20 of {len(roles)} roles")
            await ctx.send(embed=embed)
    
    @commands.command(name="createrole", aliases=["cr", "newrole"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_roles=True
    )
    async def create_role(self, ctx, *, role_name: str):
        """Create a new role"""
        # Check if role already exists
        if discord.utils.get(ctx.guild.roles, name=role_name):
            await ctx.send(f"❌ Role '{role_name}' already exists.")
            return
        
        try:
            role = await ctx.guild.create_role(
                name=role_name,
                reason=f"Created by {ctx.author.name}"
            )
            embed = discord.Embed(
                title="✅ Role Created",
                description=f"Role {role.mention} has been created.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create roles.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @commands.command(name="deleterole", aliases=["dr"])
    @commands.has_permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_roles=True
    )
    async def delete_role(self, ctx, *, role_name: str):
        """Delete a role"""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            await ctx.send(f"❌ Role '{role_name}' not found.")
            return
        
        # Check if bot can manage this role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send("❌ I don't have permission to delete this role (it's higher than my highest role).")
            return
        
        try:
            await role.delete(reason=f"Deleted by {ctx.author.name}")
            embed = discord.Embed(
                title="✅ Role Deleted",
                description=f"Role '{role_name}' has been deleted.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete roles.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @assign_role.error
    @remove_role.error
    @create_role.error
    @delete_role.error
    @list_roles.error
    async def role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            await ctx.send(f"❌ Missing required permissions: {', '.join(missing_perms)}")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Please provide all required arguments. Use `!help` for command usage.")

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))

