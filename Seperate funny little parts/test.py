import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- CONFIGURATION ---
SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=[r"C:\Users\alexn\whatsapp-mcp\whatsapp-mcp-server\main.py"],
    env=None
)

async def scrape_clean_messages(limit_total=1000):
    messages_only = []
    
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("📋 Fetching chats...")
            chats_resp = await session.call_tool("list_chats", arguments={"limit": 100})
            
            if not chats_resp.content:
                return

            # Parse chat list
            all_chats = []
            for item in chats_resp.content:
                try:
                    data = json.loads(item.text)
                    if isinstance(data, list): all_chats.extend(data)
                    elif isinstance(data, dict): all_chats.append(data)
                except: continue

            print(f"🔎 Extracting sent messages from {len(all_chats)} chats...")

            for chat in all_chats:
                if len(messages_only) >= limit_total:
                    break
                
                chat_jid = chat.get("jid") or chat.get("id")
                
                try:
                    msg_resp = await session.call_tool(
                        "list_messages", 
                        arguments={"chat_jid": chat_jid, "limit": 100}
                    )
                    
                    if not msg_resp.content:
                        continue

                    for msg_item in msg_resp.content:
                        try:
                            msg_data = json.loads(msg_item.text)
                            
                            # Filter for your messages only
                            if msg_data.get("is_from_me") == 1:
                                content = msg_data.get("content", "").strip()
                                
                                # Only add if the message isn't empty (skips blank media captions)
                                if content:
                                    messages_only.append(content)
                                
                                if len(messages_only) >= limit_total:
                                    break
                        except:
                            continue
                                
                except:
                    continue

            # --- SAVE TO TXT ---
            if messages_only:
                with open('my_messages.txt', 'w', encoding='utf-8') as f:
                    for msg in messages_only:
                        f.write(f"{msg}\n")
                
                print(f"\n✅ Done! Saved {len(messages_only)} messages to my_messages.txt")
            else:
                print("\n❌ No messages found.")

if __name__ == "__main__":
    asyncio.run(scrape_clean_messages(1000))
