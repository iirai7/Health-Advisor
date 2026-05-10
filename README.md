# 🏥 Health Advisor - AI Medical Assistant

An intelligent, bilingual (Arabic/English) healthcare platform designed to provide preliminary medical guidance using advanced AI. This project features a glassmorphism UI and a hands-free Voice Assistant for accessible healthcare.

---

## 🌟 Key Features

*   **🤖 AI Diagnosis**: Powered by high-performance LLMs (Groq/Llama) to provide instant health insights.
*   **🎙️ Voice Assistant**: Hands-free interface using browser-native **Web Speech API** for real-time STT and TTS in Arabic and English.
*   **🌍 Bilingual Support**: Full support for English and Arabic (RTL) with dynamic language switching.
*   **👨‍👩‍👧‍👦 Family Management**: Manage medical profiles for multiple family members in one account.
*   **📜 Medical History**: Persistent storage of diagnosis sessions and medical records.
*   **🚨 Emergency Detection**: Automated detection of critical symptoms with instant visual alerts.
*   **💎 Premium UI**: Modern glassmorphism design optimized for both mobile and desktop.

---

## 🚀 Technology Stack

*   **Backend**: Python / Flask
*   **Database**: MySQL
*   **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
*   **AI Integration**: Groq API (Llama 3.1)
*   **Voice Engine**: Browser Web Speech API (STT: SpeechRecognition, TTS: SpeechSynthesis)

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd diagnosis
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secret_key
   DB_HOST=localhost
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=diagnosis_db
   GROQ_API_KEY=your_groq_api_key
   ```

5. **Run the Application**:
   ```bash
   python run.py
   ```

---

## 📝 Recent Updates

*   **Voice Mode**: Added a dedicated `/voice` interface for hands-free interaction.
*   **Connection Stability**: Implemented database `ping` logic to prevent timeouts during idle sessions.
*   **Bilingual TTS**: Added automatic language detection for voice responses.

---

## 🔒 Security & Privacy

The Health Advisor is designed with privacy in mind. All medical data is encrypted and handled securely within your own database instance.

---

## ⚖️ Disclaimer

*Health Advisor is an AI-powered tool for **informational purposes only**. It does not provide professional medical diagnosis, treatment, or advice. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.*
