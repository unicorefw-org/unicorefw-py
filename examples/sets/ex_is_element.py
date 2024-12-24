# Checks if an object is an XML element (similar to DOM element).

from xml.etree.ElementTree import Element

result = UniCoreFW.is_element(Element("tag"))
print(result)  # Output: True

result = UniCoreFW.is_element("not an element")
print(result)  # Output: False
