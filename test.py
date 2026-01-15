from fastmcp import FastMCP
import random


# how to run
# Step 1: terminal 1: uv run main.py  
# Step 2: terminal 2: npx @modelcontextprotocol/inspector
# Step 3: paste this localhost url and /mcp i.e 
#         http://0.0.0.0:8000/mcp in url field
# if __name__ == "__main__":
    # mcp.run(transport='http', , host='0.0.0.0', port=8000)


mcp = FastMCP("testing-mcp", host='0.0.0.0', port=8000)

@mcp.tool()
def add(a:int, b:int)-> int:
    """add two numbers together"""
    
    return int(a + b)

@mcp.tool()
def random_number_generator(min_num:int, max_num:int=100):
    """
    generate random numbers btween min_num and max_number
    """    
    return random.randint(min_num, max_num)


if __name__ == "__main__":
    mcp.run(transport='http')


