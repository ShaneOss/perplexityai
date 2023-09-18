# NOTE: This stopped working due to Javascript/Bot checks after they moved to Cloudflare. For a working version using Selenium see: https://github.com/ShaneOss/perplexitylabs/tree/main

# perplexityai
A python api to use labs.perplexity.ai

# Usage
You can just import the Perplexity class and use it like this:
```python
from Perplexity import Perplexity

perplexity = Perplexity()
answer = perplexity.search("What is the meaning of life?")
print(answer)
```
# The model used can be updated in Perplexity.py
    #Available Models
    # llama-2-7b-chat
    # llama-2-13b-chat
    # llama-2-70b-chat
    self.model = "llama-2-70b-chat"

You can even create a cli tool with it:
```python
from Perplexity import Perplexity

perplexity = Perplexity()

while True:
    inp = str(input("> "))
    c = perplexity.search(inp)
    if c:
        print(c)
```
