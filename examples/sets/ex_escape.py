# Escapes HTML characters in a string.

result = UniCoreFW.escape("<div>Some 'text' & more</div>")
print(result)  # Output: "&lt;div&gt;Some &#x27;text&#x27; &amp; more&lt;/div&gt;"
