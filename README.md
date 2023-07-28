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
