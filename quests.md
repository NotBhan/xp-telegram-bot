# 🗡️ Quest List for XP Telegram Bot

This document contains the structured quests for your gamified life system.  
Quests are divided into categories and difficulty levels, with rewards that scale by player level.

---

## 🎵 Music Production Quests

### Easy
- Make 1 loop (drums, melody, or texture)  
- Organize 5 samples in your library  
- Adjust mix levels on 1 track  
- Export a 30-second draft idea  

### Medium
- Finish arranging 1 full song idea  
- Layer sounds for a richer texture  
- Post a short clip on Instagram  
- Design 2 original drum sounds  

### Hard
- Complete a full mixdown of a track  
- Master a finished track (basic mastering)  
- Build a mini sample pack (5–10 sounds)  
- Submit track to streaming platform or share online  

---

## 📈 Business / Store Quests

### Easy
- Reply to 1 message or comment  
- Update 1 product description in your store  
- Research 1 trending audio niche  

### Medium
- Create and post a promo reel/story  
- Design cover art for 1 sample pack  
- Write a blog or description post about your work  

### Hard
- Launch a new sample pack  
- Run a week-long IG content streak  
- Reach out to 3 potential collaborators  

---

## 🧘 Personal Growth Quests

### Easy
- Read 5 pages of a book  
- Meditate 5 minutes  
- Journal 3 sentences  

### Medium
- Exercise for 30 minutes  
- Complete a deep work session (90 minutes focus)  
- Study music theory or production for 30 minutes  

### Hard
- Finish a full book  
- Take on a 7-day streak of daily meditation/journaling  
- Build and share a tutorial/resource  

---

## 🌟 Side Quests (Random / Fun)

*(Triggered occasionally, not daily)*  
- Take a walk outside and record 3 natural sounds  
- Share a meme related to music/production  
- Write down 3 things you’re grateful for  
- Clean your workspace before working  
- Teach someone 1 small thing you learned today  

---

## ⚙️ Rewards Formula

Rewards scale with user **Level (L)**:

- **Easy Quest** → `5 * (1 + 0.1 * L)` XP + 10 Runes  
- **Medium Quest** → `10 * (1 + 0.15 * L)` XP + 20 Runes  
- **Hard Quest** → `15 * (1 + 0.2 * L)` XP + 30 Runes  
- **Side Quest** → Randomized XP + Rune reward (scaled with level)  

---

## 📋 Integration Notes

- All quests can be pre-populated in the **Quest Log Notion DB**.  
- Use the **Difficulty** property (`Easy`, `Medium`, `Hard`) to categorize.  
- The bot should **randomly select daily quests** (1 Easy, 1 Medium, 1 Hard).  
- Side quests should be triggered randomly on interval days.  
