from fastmcp import FastMCP


mcp = FastMCP.as_proxy(
    "https://mobile-emerald-guineafowl.fastmcp.app/mcp",
    name = "remote test proxy"
)


if __name__ == "__main__":
    mcp.run()