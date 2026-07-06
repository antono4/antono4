<div align="center">

<!-- Typing Animation -->
<style>
@keyframes fadeIn {
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
}
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}
@keyframes glow {
  0%, 100% { text-shadow: 0 0 5px #58A6FF, 0 0 10px #58A6FF, 0 0 20px #58A6FF; }
  50% { text-shadow: 0 0 10px #58A6FF, 0 0 20px #58A6FF, 0 0 30px #58A6FF, 0 0 40px #58A6FF; }
}
@keyframes gradient {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
@keyframes typing {
  from { width: 0; }
  to { width: 100%; }
}
@keyframes blink {
  50% { border-color: transparent; }
}
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}
@keyframes sparkle {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.animate-fade-in {
  animation: fadeIn 1s ease-out forwards;
}
.animate-float {
  animation: float 3s ease-in-out infinite;
}
.animate-glow {
  animation: glow 2s ease-in-out infinite;
}
.animate-pulse {
  animation: pulse 2s ease-in-out infinite;
}
.animate-bounce {
  animation: bounce 1s ease-in-out infinite;
}
.animate-rotate {
  animation: rotate 10s linear infinite;
}
</style>

<!-- Animated Introduction -->
<div style="background: linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%); background-size: 400% 400%; animation: gradient 15s ease infinite; padding: 40px 20px; border-radius: 20px; margin-bottom: 30px;">

### 👋 Hi, I'm <span class="animate-glow" style="color: #58A6FF; font-size: 1.2em;">Antono</span>

<p style="font-size: 1.1em;">
<span class="animate-float">🔬</span> <em>"I craft digital experiences where science meets creativity"</em> <span class="animate-float">⚡</span>
</p>

<span class="animate-bounce" style="font-size: 2em;">👨‍💻</span>

A passionate **Fullstack Developer** & **Computational Chemist** from Indonesia 🇮🇩. I transform complex problems into elegant solutions through code.

<p align="center">
  <a href="https://github.com/antono4" target="_blank" class="animate-pulse">
    <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
  <a href="https://linkedin.com/in/antono4" target="_blank" class="animate-pulse" style="animation-delay: 0.2s;">
    <img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
  <a href="https://twitter.com/antono4" target="_blank" class="animate-pulse" style="animation-delay: 0.4s;">
    <img src="https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white" alt="Twitter">
  </a>
  <a href="mailto:antono4@example.com" target="_blank" class="animate-pulse" style="animation-delay: 0.6s;">
    <img src="https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Email">
  </a>
</p>

<!-- Decorative floating elements -->
<span class="animate-float" style="position: absolute; left: 10%; font-size: 1.5em;">☕</span>
<span class="animate-float" style="position: absolute; right: 10%; animation-delay: 1s; font-size: 1.5em;">🚀</span>
<span class="animate-float" style="position: absolute; left: 5%; top: 60%; animation-delay: 0.5s; font-size: 1.2em;">💡</span>
<span class="animate-float" style="position: absolute; right: 5%; top: 60%; animation-delay: 1.5s; font-size: 1.2em;">🎮</span>

</div>

---

## 🎯 Quick Stats

<div align="center">

| <img src="https://github-readme-stats.vercel.app/api?username=antono4&theme=transparent&bg_color=0D1117&text_color=58A6FF&border_color=30363D&hide_rank=true" width="200"/> | <img src="https://streak-stats.demolab.com?user=Antono4&date_format=j%20M%5B%20Y%5D&mode=weekly&background=0D1117&border=30363D&stroke=58A6FF&ring=58A6FF&fire=58A6FF&currStreakNum=58A6FF&sideNums=58A6FF&currStreakLabel=58A6FF&sideLabels=58A6FF&nextDuelMsg=58A6FF" width="200"/> | <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=antono4&theme=transparent&bg_color=0D1117&text_color=58A6FF&border_color=30363D&layout=compact&hide_progress=false" width="200"/> |
|:---:|:---:|:---:|
| **Profile Views** | **Contribution Streak** | **Top Languages** |

</div>

---

## 🛠️ Tech Arsenal

<style>
.tech-card {
  background: linear-gradient(145deg, #161B22, #0D1117);
  border: 1px solid #30363D;
  border-radius: 12px;
  padding: 20px;
  margin: 15px 0;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.tech-card:hover {
  transform: translateY(-5px);
  border-color: #58A6FF;
  box-shadow: 0 10px 40px rgba(88, 166, 255, 0.2);
}
.tech-card::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(88, 166, 255, 0.1) 0%, transparent 70%);
  animation: rotate 20s linear infinite;
}
@keyframes rainbow-border {
  0% { border-color: #FF6B6B; }
  25% { border-color: #4ECDC4; }
  50% { border-color: #45B7D1; }
  75% { border-color: #96CEB4; }
  100% { border-color: #FF6B6B; }
}
.rainbow-border {
  animation: rainbow-border 5s linear infinite;
}
.fun-fact-card {
  background: linear-gradient(135deg, #161B22 0%, #1a1f26 50%, #161B22 100%);
  border: 1px solid #30363D;
  border-radius: 16px;
  padding: 30px;
  margin: 20px 0;
  position: relative;
}
.fun-fact-card:hover {
  border-color: #58A6FF;
  box-shadow: 0 0 30px rgba(88, 166, 255, 0.15);
}
.fact-item {
  padding: 10px 0;
  transition: all 0.3s ease;
}
.fact-item:hover {
  padding-left: 10px;
  background: rgba(88, 166, 255, 0.05);
  border-radius: 8px;
}
</style>

<div class="tech-card rainbow-border">

### 💻 Languages
<p align="center">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript"/>
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/PHP-777BB4?style=for-the-badge&logo=php&logoColor=white" alt="PHP"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Go-00ADD8?style=for-the-badge&logo=go&logoColor=white" alt="Go"/>
</p>

<div class="tech-card">
### ⚛️ Frontend
<p align="center">
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js"/>
  <img src="https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white" alt="Angular"/>
  <img src="https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white" alt="Vue.js"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind"/>
</p>
</div>

<div class="tech-card">
### ⚙️ Backend & Database
<p align="center">
  <img src="https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white" alt="Node.js"/>
  <img src="https://img.shields.io/badge/NestJS-E0234E?style=for-the-badge&logo=nestjs&logoColor=white" alt="NestJS"/>
  <img src="https://img.shields.io/badge/GraphQL-E10098?style=for-the-badge&logo=graphql&logoColor=white" alt="GraphQL"/>
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/>
</p>
</div>

<div class="tech-card">
### 🐳 DevOps & Cloud
<p align="center">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" alt="GitHub Actions"/>
  <img src="https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" alt="GCP"/>
  <img src="https://img.shields.io/badge/AWS-FF9900?style=for-the-badge&logo=amazonaws&logoColor=black" alt="AWS"/>
  <img src="https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux"/>
</p>
</div>

---

## 📊 Activity

<style>
.activity-card {
  background: linear-gradient(145deg, #161B22, #0D1117);
  border-radius: 16px;
  padding: 25px;
  margin: 20px 0;
  border: 1px solid #30363D;
  position: relative;
  overflow: hidden;
}
.activity-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(88, 166, 255, 0.1), transparent);
  animation: shimmer 3s infinite;
}
</style>

<div class="activity-card">

![Contribution Graph](https://github-readme-activity-graph.vercel.app/graph?username=antono4&theme=github_dark&area=true&hide_border=true&bg_color=0D1117&color=58A6FF&line=58A6FF&point=58A6FF&area_color=1F6FEB)

![Snake Animation](https://github.com/antono4/antono4/raw/output/github-contribution-grid-snake.svg)

</div>

---

## 🏆 Achievements

<div align="center">

[![Trophy](https://github-profile-trophy.vercel.app/?username=antono4&theme=onedark&margin-w=15&margin-h=15)](https://github.com/antono4)
[![Streak](https://streak-stats.demolab.com?user=Antono4&date_format=j%20M%5B%20Y%5D&mode=weekly&background=0D1117&border=30363D&stroke=58A6FF&ring=58A6FF&fire=58A6FF&currStreakNum=58A6FF&sideNums=58A6FF&currStreakLabel=58A6FF&sideLabels=58A6FF&nextDuelMsg=58A6FF)](https://git.io/streak-stats)

</div>

---

## 💡 Fun Facts

<div class="fun-fact-card" align="center">

<div class="fact-item">🧪 Former computational chemist turned software engineer</div>
<div class="fact-item">☕ Powered by coffee and curiosity</div>
<div class="fact-item">🌙 Night owl coder</div>
<div class="fact-item">🎮 Gaming enthusiast</div>
<div class="fact-item">📚 Always learning something new</div>

</div>

---

## 📝 Latest Blog Posts

<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->

---

<style>
.footer-card {
  background: linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%);
  border-top: 1px solid #30363D;
  border-radius: 20px 20px 0 0;
  padding: 30px;
  margin-top: 30px;
  position: relative;
  overflow: hidden;
}
.sparkle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #58A6FF;
  border-radius: 50%;
  animation: sparkle 2s ease-in-out infinite;
}
.sparkle:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; }
.sparkle:nth-child(2) { top: 40%; right: 15%; animation-delay: 0.5s; }
.sparkle:nth-child(3) { bottom: 30%; left: 20%; animation-delay: 1s; }
.sparkle:nth-child(4) { top: 10%; right: 30%; animation-delay: 1.5s; }
</style>

<div class="footer-card">

<span class="sparkle"></span>
<span class="sparkle"></span>
<span class="sparkle"></span>
<span class="sparkle"></span>

![Profile Views](https://komarev.com/ghpvc/?username=antono4&color=58A6FF&style=for-the-badge&label=Profile+Views)

<span class="animate-bounce">⭐️</span> From [antono4](https://github.com/antono4)

<span class="animate-float" style="display: block; margin-top: 15px; font-size: 1.2em;">🚀 Let's build something amazing together!</span>

</div>
