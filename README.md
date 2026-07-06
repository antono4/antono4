<div align="center">

<!-- Enhanced Animations -->
<style>
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
}

@keyframes glow {
  0%, 100% { text-shadow: 0 0 5px #58A6FF, 0 0 10px #58A6FF, 0 0 20px #58A6FF; }
  50% { text-shadow: 0 0 10px #79C0FF, 0 0 20px #79C0FF, 0 0 40px #79C0FF, 0 0 60px #58A6FF; }
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

@keyframes pulse-scale {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}

@keyframes bounce-subtle {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

@keyframes rotate-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}

@keyframes sparkle {
  0%, 100% { opacity: 1; transform: scale(1) rotate(0deg); }
  50% { opacity: 0.4; transform: scale(0.6) rotate(180deg); }
}

@keyframes typing {
  from { width: 0; }
  to { width: 100%; }
}

@keyframes blink {
  0%, 50% { border-color: #58A6FF; }
  51%, 100% { border-color: transparent; }
}

/* Main Container */
.main-container {
  background: linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%);
  background-size: 400% 400%;
  animation: gradient-shift 15s ease infinite;
  padding: 50px 30px;
  border-radius: 24px;
  margin-bottom: 30px;
  position: relative;
  overflow: hidden;
  border: 1px solid #30363D;
}

.main-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(88, 166, 255, 0.05) 0%, transparent 50%);
  animation: rotate-slow 30s linear infinite;
}

/* Particle Effects */
.particle {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: sparkle 3s ease-in-out infinite;
}

.particle:nth-child(1) { top: 10%; left: 5%; background: #58A6FF; animation-delay: 0s; }
.particle:nth-child(2) { top: 20%; right: 10%; background: #A371F7; animation-delay: 0.5s; }
.particle:nth-child(3) { top: 60%; left: 8%; background: #3FB950; animation-delay: 1s; }
.particle:nth-child(4) { top: 70%; right: 15%; background: #F0883E; animation-delay: 1.5s; }
.particle:nth-child(5) { top: 40%; left: 15%; background: #DB61A2; animation-delay: 2s; }
.particle:nth-child(6) { top: 30%; right: 5%; background: #79C0FF; animation-delay: 2.5s; }

/* Profile Ring Animation */
.profile-wrapper {
  position: relative;
  width: 150px;
  height: 150px;
  margin: 0 auto 25px;
}

.profile-ring {
  position: absolute;
  inset: -5px;
  border-radius: 50%;
  border: 3px solid transparent;
  border-top-color: #58A6FF;
  border-right-color: #A371F7;
  animation: rotate-slow 3s linear infinite;
}

.profile-ring::before {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: 50%;
  border: 3px solid transparent;
  border-bottom-color: #3FB950;
  border-left-color: #79C0FF;
  animation: rotate-slow 2s linear infinite reverse;
}

/* Hero Typography */
.hero-title {
  font-size: 3em;
  font-weight: 700;
  color: #fff;
  margin-bottom: 15px;
  animation: glow 3s ease-in-out infinite;
}

.hero-title span {
  background: linear-gradient(90deg, #58A6FF, #A371F7, #79C0FF);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 3s ease infinite;
}

.typing-text {
  font-family: 'Courier New', monospace;
  font-size: 1.1em;
  color: #79C0FF;
  overflow: hidden;
  white-space: nowrap;
  border-right: 3px solid #58A6FF;
  animation: typing 4s steps(50) 1s forwards, blink 0.8s step-end infinite;
  max-width: 100%;
}

/* Floating Elements */
.float-element { animation: float 4s ease-in-out infinite; }
.float-delay-1 { animation-delay: 0s; }
.float-delay-2 { animation-delay: 0.5s; }
.float-delay-3 { animation-delay: 1s; }
.float-delay-4 { animation-delay: 1.5s; }
.float-delay-5 { animation-delay: 2s; }

/* Social Links */
.social-links {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 25px;
  flex-wrap: wrap;
}

.social-btn {
  position: relative;
  padding: 10px 20px;
  border-radius: 12px;
  background: rgba(22, 27, 34, 0.8);
  border: 1px solid #30363D;
  transition: all 0.3s ease;
  overflow: hidden;
}

.social-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: rgba(88, 166, 255, 0.2);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: all 0.5s ease;
}

.social-btn:hover::before {
  width: 300px;
  height: 300px;
}

.social-btn:hover {
  transform: translateY(-5px) scale(1.05);
  border-color: #58A6FF;
  box-shadow: 0 10px 30px rgba(88, 166, 255, 0.3);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin: 25px 0;
}

.stat-card {
  background: linear-gradient(145deg, #161B22, #0D1117);
  border: 1px solid #30363D;
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  transition: all 0.4s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(88, 166, 255, 0.1), transparent);
  transition: all 0.5s ease;
}

.stat-card:hover::after { left: 100%; }

.stat-card:hover {
  transform: translateY(-8px) scale(1.02);
  border-color: #58A6FF;
  box-shadow: 0 15px 40px rgba(88, 166, 255, 0.2);
}

.stat-card:nth-child(1):hover { border-color: #58A6FF; }
.stat-card:nth-child(2):hover { border-color: #F0883E; }
.stat-card:nth-child(3):hover { border-color: #3FB950; }

/* Tech Cards */
.tech-card {
  background: linear-gradient(145deg, #161B22, #0D1117);
  border: 1px solid #30363D;
  border-radius: 16px;
  padding: 25px;
  margin: 20px 0;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  overflow: hidden;
}

.tech-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #58A6FF, #A371F7, #79C0FF);
  background-size: 200% auto;
  animation: gradient-shift 3s ease infinite;
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.tech-card:hover::before { transform: scaleX(1); }

.tech-card:hover {
  transform: translateY(-10px);
  border-color: #58A6FF;
  box-shadow: 0 20px 50px rgba(88, 166, 255, 0.15);
}

.tech-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-top: 15px;
}

.tech-badge {
  padding: 8px 15px;
  border-radius: 20px;
  background: rgba(88, 166, 255, 0.1);
  border: 1px solid rgba(88, 166, 255, 0.2);
  transition: all 0.3s ease;
  font-size: 0.9em;
}

.tech-badge:hover {
  background: rgba(88, 166, 255, 0.2);
  transform: scale(1.1);
  box-shadow: 0 5px 15px rgba(88, 166, 255, 0.2);
}

/* Activity Wrapper */
.activity-wrapper {
  background: linear-gradient(145deg, #161B22, #0D1117);
  border: 1px solid #30363D;
  border-radius: 20px;
  padding: 30px;
  margin: 25px 0;
  position: relative;
  overflow: hidden;
}

.activity-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #58A6FF, #A371F7, #3FB950, #F0883E);
  background-size: 300% auto;
  animation: gradient-shift 4s ease infinite;
}

/* Achievements */
.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.achievement-card {
  background: linear-gradient(145deg, #161B22, #0D1117);
  border: 1px solid #30363D;
  border-radius: 16px;
  padding: 25px;
  text-align: center;
  transition: all 0.4s ease;
}

.achievement-card:hover {
  transform: translateY(-5px) rotateX(5deg);
  border-color: gold;
  box-shadow: 0 10px 30px rgba(255, 215, 0, 0.2);
}

/* Fun Facts */
.fun-fact-container {
  background: linear-gradient(135deg, #161B22 0%, #0D1117 100%);
  border: 1px solid #30363D;
  border-radius: 20px;
  padding: 35px;
  margin: 25px 0;
  position: relative;
}

.fun-fact-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  margin: 10px 0;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid transparent;
  transition: all 0.3s ease;
  cursor: default;
}

.fun-fact-item:hover {
  background: rgba(88, 166, 255, 0.08);
  border-color: #58A6FF;
  transform: translateX(10px);
  padding-left: 25px;
}

.fact-emoji {
  font-size: 1.8em;
  animation: bounce-subtle 2s ease-in-out infinite;
}

.fun-fact-item:nth-child(1) .fact-emoji { animation-delay: 0s; }
.fun-fact-item:nth-child(2) .fact-emoji { animation-delay: 0.2s; }
.fun-fact-item:nth-child(3) .fact-emoji { animation-delay: 0.4s; }
.fun-fact-item:nth-child(4) .fact-emoji { animation-delay: 0.6s; }
.fun-fact-item:nth-child(5) .fact-emoji { animation-delay: 0.8s; }

/* Footer */
.footer {
  background: linear-gradient(180deg, #0D1117 0%, rgba(13, 17, 23, 0.95) 100%);
  border-top: 1px solid #30363D;
  border-radius: 24px 24px 0 0;
  padding: 40px 30px;
  margin-top: 30px;
  position: relative;
  overflow: hidden;
  text-align: center;
}

.footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #58A6FF, #A371F7, #DB61A2, #F0883E);
  background-size: 300% auto;
  animation: gradient-shift 4s ease infinite;
}

.visitor-counter {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 25px;
  background: rgba(88, 166, 255, 0.1);
  border: 1px solid rgba(88, 166, 255, 0.3);
  border-radius: 50px;
  margin-bottom: 20px;
}

.heart {
  color: #ff6b6b;
  animation: pulse-scale 1.5s ease-in-out infinite;
}

.final-message {
  font-size: 1.3em;
  color: #fff;
  margin-top: 20px;
}

.cta-btn {
  display: inline-block;
  padding: 15px 35px;
  margin-top: 25px;
  background: linear-gradient(135deg, #58A6FF, #A371F7);
  background-size: 200% auto;
  border: none;
  border-radius: 50px;
  color: #fff;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  animation: gradient-shift 3s ease infinite;
  text-decoration: none;
}

.cta-btn:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 10px 30px rgba(88, 166, 255, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .hero-title { font-size: 2em; }
  .stats-grid { grid-template-columns: 1fr; }
  .main-container { padding: 30px 20px; }
}
</style>

<!-- Main Container with Particles -->
<div class="main-container">
  <!-- Floating Particles -->
  <span class="particle"></span>
  <span class="particle"></span>
  <span class="particle"></span>
  <span class="particle"></span>
  <span class="particle"></span>
  <span class="particle"></span>

  <!-- Profile Ring -->
  <div class="profile-wrapper">
    <div class="profile-ring"></div>
    <span class="float-element" style="font-size: 80px; display: flex; align-items: center; justify-content: center;">👨‍💻</span>
  </div>

  <!-- Hero Title -->
  <h1 class="hero-title">
    👋 Hi, I'm <span>Antono</span>
  </h1>

  <!-- Typing Effect -->
  <div class="typing-text">
    🔬 "I craft digital experiences where science meets creativity" ⚡
  </div>

  <!-- Bio -->
  <p style="margin-top: 20px; font-size: 1.1em; color: #c9d1d9; max-width: 600px; margin-left: auto; margin-right: auto;">
    A passionate <strong style="color: #58A6FF;">Fullstack Developer</strong> & 
    <strong style="color: #A371F7;">Computational Chemist</strong> from 
    <strong style="color: #3FB950;">Indonesia 🇮🇩</strong>. 
    I transform complex problems into elegant solutions through code.
  </p>

  <!-- Social Links -->
  <div class="social-links">
    <a href="https://github.com/antono4" target="_blank" class="social-btn">
      <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/>
    </a>
    <a href="https://linkedin.com/in/antono4" target="_blank" class="social-btn">
      <img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"/>
    </a>
    <a href="https://twitter.com/antono4" target="_blank" class="social-btn">
      <img src="https://img.shields.io/badge/Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white" alt="Twitter"/>
    </a>
    <a href="mailto:antono4@example.com" target="_blank" class="social-btn">
      <img src="https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"/>
    </a>
  </div>

  <!-- Floating Emojis -->
  <div style="position: absolute; top: 20px; left: 30px;">
    <span class="float-element float-delay-1" style="font-size: 2em;">☕</span>
  </div>
  <div style="position: absolute; top: 40px; right: 40px;">
    <span class="float-element float-delay-2" style="font-size: 1.8em;">🚀</span>
  </div>
  <div style="position: absolute; bottom: 80px; left: 50px;">
    <span class="float-element float-delay-3" style="font-size: 1.6em;">💡</span>
  </div>
  <div style="position: absolute; bottom: 60px; right: 60px;">
    <span class="float-element float-delay-4" style="font-size: 1.7em;">🎮</span>
  </div>
  <div style="position: absolute; top: 100px; left: 20%;">
    <span class="float-element float-delay-5" style="font-size: 1.5em;">⚛️</span>
  </div>
</div>

---

## 🎯 Quick Stats

<div class="stats-grid">
  <div class="stat-card">
    <img src="https://github-readme-stats.vercel.app/api?username=antono4&theme=transparent&bg_color=0D1117&text_color=58A6FF&border_color=30363D&hide_rank=true&include_all_commits=true&count_private=true" width="100%" alt="Stats"/>
  </div>
  <div class="stat-card">
    <img src="https://streak-stats.demolab.com?user=Antono4&date_format=j%20M%5B%20Y%5D&mode=weekly&background=0D1117&border=30363D&stroke=58A6FF&ring=F0883E&fire=F0883E&currStreakNum=F0883E&sideNums=F0883E&currStreakLabel=F0883E&sideLabels=F0883E&nextDuelMsg=F0883E" width="100%" alt="Streak"/>
  </div>
  <div class="stat-card">
    <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=antono4&theme=transparent&bg_color=0D1117&text_color=3FB950&border_color=30363D&layout=compact" width="100%" alt="Languages"/>
  </div>
</div>

---

## 🛠️ Tech Arsenal

### 💻 Languages
<div class="tech-card">
  <div class="tech-badges">
    <span class="tech-badge">☕ JavaScript</span>
    <span class="tech-badge">🔷 TypeScript</span>
    <span class="tech-badge">🐘 PHP</span>
    <span class="tech-badge">🐍 Python</span>
    <span class="tech-badge">🔵 Go</span>
  </div>
</div>

### ⚛️ Frontend
<div class="tech-card">
  <div class="tech-badges">
    <span class="tech-badge">⚛️ React</span>
    <span class="tech-badge">▲ Next.js</span>
    <span class="tech-badge">🔴 Angular</span>
    <span class="tech-badge">💚 Vue.js</span>
    <span class="tech-badge">💨 Tailwind</span>
  </div>
</div>

### ⚙️ Backend & Database
<div class="tech-card">
  <div class="tech-badges">
    <span class="tech-badge">🟢 Node.js</span>
    <span class="tech-badge">🦅 NestJS</span>
    <span class="tech-badge">◈ GraphQL</span>
    <span class="tech-badge">🐘 PostgreSQL</span>
    <span class="tech-badge">🍃 MongoDB</span>
  </div>
</div>

### 🐳 DevOps & Cloud
<div class="tech-card">
  <div class="tech-badges">
    <span class="tech-badge">🐳 Docker</span>
    <span class="tech-badge">⚡ GitHub Actions</span>
    <span class="tech-badge">☁️ GCP</span>
    <span class="tech-badge">🟠 AWS</span>
    <span class="tech-badge">🐧 Linux</span>
  </div>
</div>

---

## 📊 Activity

<div class="activity-wrapper">
  <p style="text-align: center; margin-bottom: 20px; color: #79C0FF;">
    ✨ Contribution Graph
  </p>
  <img src="https://github-readme-activity-graph.vercel.app/graph?username=antono4&theme=github_dark&area=true&hide_border=true&bg_color=0D1117&color=58A6FF&line=58A6FF&point=58A6FF&area_color=1F6FEB" width="100%" alt="Activity Graph"/>
  
  <div style="margin-top: 20px;" align="center">
    <img src="https://github.com/antono4/antono4/raw/output/github-contribution-grid-snake.svg" alt="Snake Animation"/>
  </div>
</div>

---

## 🏆 Achievements

<div class="achievements-grid">
  <div class="achievement-card">
    <img src="https://github-profile-trophy.vercel.app/?username=antono4&theme=onedark&margin-w=15&margin-h=15" width="100%" alt="Trophy"/>
  </div>
  <div class="achievement-card">
    <img src="https://streak-stats.demolab.com?user=Antono4&date_format=j%20M%5B%20Y%5D&mode=weekly&background=0D1117&border=30363D&stroke=58A6FF&ring=58A6FF&fire=58A6FF&currStreakNum=58A6FF&sideNums=58A6FF&currStreakLabel=58A6FF&sideLabels=58A6FF&nextDuelMsg=58A6FF" width="100%" alt="Streak Stats"/>
  </div>
</div>

---

## 💡 Fun Facts

<div class="fun-fact-container">
  <div class="fun-fact-item">
    <span class="fact-emoji">🧪</span>
    <span>Former computational chemist turned software engineer</span>
  </div>
  <div class="fun-fact-item">
    <span class="fact-emoji">☕</span>
    <span>Powered by coffee and curiosity</span>
  </div>
  <div class="fun-fact-item">
    <span class="fact-emoji">🌙</span>
    <span>Night owl coder</span>
  </div>
  <div class="fun-fact-item">
    <span class="fact-emoji">🎮</span>
    <span>Gaming enthusiast</span>
  </div>
  <div class="fun-fact-item">
    <span class="fact-emoji">📚</span>
    <span>Always learning something new</span>
  </div>
</div>

---

## 📝 Latest Blog Posts

<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->

---

<!-- Footer -->
<div class="footer">
  <div class="visitor-counter">
    <img src="https://komarev.com/ghpvc/?username=antono4&color=58A6FF&style=for-the-badge&label=Profile+Views" alt="Visitor Count"/>
  </div>
  
  <p class="final-message">
    Made with <span class="heart">❤️</span> by <strong style="color: #58A6FF;">Antono</strong>
  </p>
  
  <p style="color: #8b949e; margin-top: 10px;">
    ⭐️ From Indonesia 🇮🇩
  </p>
  
  <a href="https://github.com/antono4" class="cta-btn">
    🚀 Let's Connect!
  </a>
  
  <p style="margin-top: 30px; color: #484f58; font-size: 0.9em;">
    © 2024 Antono. Crafted with passion and lots of ☕
  </p>
</div>
