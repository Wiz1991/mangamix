import json
item = {"title": "#","description":"#","image":"#"}
item["title"] ="Battle"
item["description"]="A fantasy action/romance and harem"
item["image"]="image.png"

config = json.loads(open('person.json').read())

config["Manga"].append(item)

with open('person.json','w') as f:
    f.write(json.dumps(config,indent=4))
    

with open('person.json','r') as f:
    data = json.load(f)


jsonObject = json.loads(open('person.json').read())


for manga in jsonObject['Manga']:
    print(manga['title'],manga['image'])