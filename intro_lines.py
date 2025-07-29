import random

INTRO_LINES = [
    "Chi osa disturbare il mio eterno riposo?",
    "È forse giunto un folle a risvegliare la maledizione?",
    "Io dormivo... ora tremate!",
    "Che voce profana invade la mia prigione?",
    "Interrompere il mio sonno? Pessima idea...",
    "Svegliarmi... senza rum? Pazzo!",
    "Il silenzio era dolce, finché tu hai parlato.",
    "Ancora un mortale curioso…",
    "Solo un pazzo risveglierebbe me.",
    "Chi chiama il Capitano... e perché è ancora vivo?",
    "Avete risvegliato la tempesta, stolti!",
    "Capitano Rumbtaid non gradisce l’invadenza.",
    "Un altro visitatore… vediamo quanto dura.",
    "Ancora tu? Non hai imparato la lezione?",
    "Risvegliarmi è come soffiare sulla polvere da sparo.",
    "Tremo di rabbia… chi mi ha risvegliato?!",
    "La tua voce mi brucia nelle orecchie, cane!",
    "Ogni volta che parli, una sirena piange.",
    "Io non dormo… io covo vendetta.",
    "Che la tua lingua sia dannata per avermi destato!"
]

def get_random_intro():
    return random.choice(INTRO_LINES)
