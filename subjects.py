# Fanlar: kalit -> ko'rinadigan nom
SUBJECTS = {
    "biology":   "🧬 Biologiya",
    "chemistry": "⚗️ Kimyo",
    "math":      "➗ Matematika",
    "english":   "🇬🇧 Ingliz tili",
    "native":    "📖 Ona tili",
    "huquq":     "⚖️ Huquq",
}

# Har bir yo'nalishga doir fanlar (yo'nalish nomi bot.py dagi DIRECTIONS bilan bir xil bo'lishi shart)
DIRECTION_SUBJECTS = {
    "Tibbiyot yo'nalishi":                    ["biology", "chemistry"],
    "Aniq fanlar (matematika, ingliz tili)":  ["math", "english"],
    "Yuridika":                               ["huquq", "english"],
    "Filologiya":                             ["native", "english"],
}
