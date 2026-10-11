import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- CONFIGURATION ---
SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=[r"C:\Users\alexn\whatsapp-mcp\whatsapp-mcp-server\main.py"],
    env=None
)


async def get_recent_chat_names(session):
    """
    Returns a list of all recent chat names and JIDs.
    """
    print("📋 Fetching recent chat list...")
    
    # Call the tool
    result = await session.call_tool("list_chats", arguments={"limit": 100})
    
    if not result.content:
        return []

    chats = []
    for x in range(0,100):
        data = json.loads(result.content[x].text)
        chats.append(data["name"])
    # Fallback if result is just raw text
    #print(f"Raw list: {result.content[1].text[:10000]}...")
    return chats






async def find_chat_jid(session, target_name):
    
    """
    Scans active chats and handles the specific string-list format 
    returned by your WhatsApp MCP server.
    """
    print(f"Scanning active chats for '{target_name}'...")
    
    chats_resp = await session.call_tool("list_chats", arguments={"limit": 100})
    
    if not chats_resp.content:
        print("No chat history found.")
        return None

    for content_item in chats_resp.content:
        try:
            # Your server sends back data in blocks. We check each block.
            # We try to load the text as JSON.
            data = json.loads(content_item.text)
            
            # If the server returned a list of chats at once:
            if isinstance(data, list):
                for chat in data:
                    name = chat.get("name") or ""
                    if target_name.lower() in name.lower():
                        jid = chat.get("jid") or chat.get("id")
                        print(f"Match Found: '{name}' [ID: {jid}]")
                        return jid
            
            # If the server returned a single chat object (as seen in your snippet):
            elif isinstance(data, dict):
                name = data.get("name") or ""
                if target_name.lower() in name.lower():
                    # Your snippet uses "jid", so we prioritize that
                    jid = data.get("jid") or data.get("id")
                    print(f"✅ Match Found: '{name}' [ID: {jid}]")
                    return jid

        except Exception:
            # If it's not JSON, we skip this block and keep looking
            continue
            
    return None

async def run_assistant(target_name, message_count):
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # 1. Locate the Chat ID
            jid = await find_chat_jid(session, target_name)
            
            if not jid:
                print(f"❌ Could not find a chat named '{target_name}'.")
                return

            # 2. Fetch the messages
            try:
                # Using the JID we just found
                result = await session.call_tool(
                    "send_message", 
                    arguments={
                        "recipient": jid,
                        "message": "Lucas test"
                    }
                )
                print(f"Message sent! Server response: {result.content[0].text}")
                """messages = await session.call_tool(
                    "list_messages", 
                    arguments={"chat_jid": jid, "limit": message_count}
                )
                
                print(f"\n--- LAST {message_count} MESSAGES IN '{target_name}' ---")
                
                if not messages.content:
                    print("No messages found.")
                    return

                for msg in messages.content:
                    print(f"💬 {msg.text}")"""
                    
            except Exception as e:
                print(f"❌ Error fetching messages: {e}")

if __name__ == "__main__":
    # --- TARGET SETTINGS ---

    SEARCH_FOR = input("")
    HOW_MANY = 10
    # -----------------------

    try:
        asyncio.run(run_assistant(SEARCH_FOR, HOW_MANY))
    except KeyboardInterrupt:
        print("\nStopped.")

