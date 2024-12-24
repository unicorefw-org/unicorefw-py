# Allows embedding expressions within a template string, evaluating within a context.
template = "Name: <%= name %>, Age: <%= age %>"
context = {"name": "Alice", "age": 25}
result = UniCoreFW.template(template, context)
print(result)  # Output: "Name: Alice, Age: 25"


tmpl = """Name: <% if prefix: %><%= prefix %>. <% endif %><%= name %>
Last Name: <%= lname.upper() %>
<% if email: %>
E-mail: <%= email %>
<% endif %>"""

people = [
    {"prefix": "", "name": "John", "lname": "Doe", "email": "johndoe@example.com"},
    {"prefix": "Mr", "name": "James", "lname": "Brown", "email": "james@brown.net"},
]

for person in people:
    result = UniCoreFW.template(tmpl, person)
    print(result)
    print("---")
