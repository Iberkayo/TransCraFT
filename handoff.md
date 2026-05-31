# TransCraft - Proje Devir ve Handoff Notları (31 Mayıs 2026)

Bu belge, yarın ofis bilgisayarınızdan çalışmaya devam ederken projenin durumunu hızlıca hatırlatmak ve atılacak adımları planlamak amacıyla hazırlanmıştır.

---

## 📅 Bugün Neler Yaptık ve Test Ettik?

1.  **Kod Tabanı Geliştirildi:** Çoklu ajan mimarisi (LangGraph), akıllı parçalayıcı (PDF ve TXT), durum hafızası, kurtarma sistemi (Resume) ve otonom kalite puanlayıcı (AI-as-a-Judge) tamamen entegre edildi.
2.  **Tür Bazlı Ayrım Yapıldı:** `tech` (teknik/akademik) ve `literary` (edebi/sanatsal) metinler için ayrı terim sözlükleri ve yazım kılavuzları kuruldu.
3.  **Arayüzler Entegre Edildi:** CLI konsolunun yanı sıra interaktif **Streamlit** arayüzü (`app.py`) ve arka planda servis olarak çalışabilen **FastAPI** sunucusu (`src/core/server.py`) yazıldı.
4.  **Birim Testleri:** `pytest` ile 4 çekirdek modül testi yazıldı ve hepsi başarıyla geçti (`4 passed`).
5.  **Büyük PDF Çevirisi Başarıyla Tamamlandı:** "Attention Is All You Need" yapay zeka makalesi (`1706.03762v7.pdf`) İngilizce'den Türkçe'ye otonom olarak çevrildi ve [data/outputs/translated_1706.03762v7.txt](file:///c:/Users/iberk/Documents/antigravity/nifty-volta/data/outputs/translated_1706.03762v7.txt) konumuna kaydedildi.

---

## 📂 Kod Yapısı Rehberi

*   **[app.py](file:///c:/Users/iberk/Documents/antigravity/nifty-volta/app.py):** Streamlit Web Arayüzü dosyası.
*   **[main.py](file:///c:/Users/iberk/Documents/antigravity/nifty-volta/main.py):** CLI çalıştırıcısı ve sunucu modlarını koordine eden ana giriş.
*   **[src/core/document_processor.py](file:///c:/Users/iberk/Documents/antigravity/nifty-volta/src/core/document_processor.py):** PDF okuma ve paragraf/cümle tabanlı akıllı dilimleyici.
*   **[src/core/evaluator.py](file:///c:/Users/iberk/Documents/antigravity/nifty-volta/src/core/evaluator.py):** Çeviri kalitesini değerlendiren yapay zeka hakemi.
*   **[src/core/server.py](file:///c:/Users/iberk/Documents/antigravity/nifty-volta/src/core/server.py):** FastAPI sunucu yönlendirmeleri.
*   **[src/agents/](file:///c:/Users/iberk/Documents/antigravity/nifty-volta/src/agents/):** Uzman ajanlar (Analyst, Translator, Stylist, Critic, Polisher).
*   **[data/reference/](file:///c:/Users/iberk/Documents/antigravity/nifty-volta/data/reference/):** Tür bazlı terim sözlükleri (`tech/`, `literary/`) ve genel deyimler JSON dosyası.

---

## 🏁 Yarın Ofis Bilgisayarında Yapılacaklar (Adım Adım)

1.  **Projeyi Çekin:** 
    `git clone https://github.com/Iberkayo/TransCraFT.git` komutuyla projeyi ofis bilgisayarınıza indirin.
2.  **Bağımlılıkları Kurun:**
    Proje dizinine girip `pip install -r requirements.txt` komutuyla kütüphaneleri yükleyin.
3.  **Çevre Değişkenlerini Tanımlayın:**
    Dizinde yeni bir `.env` dosyası oluşturup OpenAI API anahtarınızı yapıştırın:
    ```env
    OPENAI_API_KEY=sk-proj-...
    ```
4.  **Web Arayüzünü Çalıştırın:**
    `streamlit run app.py` komutuyla web arayüzünü açıp yeni PDF/TXT belgeleri yükleyerek canlı ajan akışlarını görsel olarak deneyimleyin.
5.  **Birim Testlerini Koşun:**
    `python -m pytest tests/` komutuyla ofis makinenizde sistemin sağlıklı kurulduğunu teyit edin.
6.  **Sözlükleri Genişletin:**
    `python src/scripts/augment_data.py` scriptini çalıştırarak İngilizce deyim havuzunu otonom olarak genişletebilir veya dikey klasörlerdeki sözlüklere yeni kelimeler ekleyebilirsiniz.
