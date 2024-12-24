# Unescapes HTML characters in a string.

result = UniCoreFW.unescape("&lt;div&gt;Some &#x27;text&#x27; &amp; more&lt;/div&gt;")
print(result)  # Output: "<div>Some 'text' & more</div>"
