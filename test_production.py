"""
Azure Production RAG Test Script
Azure'da deploy edilmiş query_function endpoint'ini test eder.
"""
import os
import requests
import json
from typing import Dict, Any

# ─────────────────────────────────────────────────────────────────────────────
# ADM 1: Azure Portal'dan aldığınız Function URL'ini buraya yapıştırın
# ─────────────────────────────────────────────────────────────────────────────
FUNCTION_URL = os.getenv("AZURE_FUNCTION_URL")
# Eğer URL'de code parametresi yoksa, ayrıca header ile gönderebilirsiniz:
# FUNCTION_KEY = "your-function-key"


def test_query(question: str) -> Dict[str, Any]:
    """
    Azure Function'a soru gönderip cevap alır.
    
    Args:
        question: Finansal soru (örn: "NVDA'nın son çeyrek geliri ne?")
    
    Returns:
        API'den dönen JSON response
    """
    headers = {
        "Content-Type": "application/json",
        # Alternatif: Function key header olarak göndermek için:
        # "x-functions-key": FUNCTION_KEY
    }
    
    payload = {
        "question": question
    }
    
    print(f"\n{'='*80}")
    print(f"SORU GÖNDERİLİYOR:")
    print(f"{'='*80}")
    print(f"Endpoint: {FUNCTION_URL.split('?')[0]}")
    print(f"Soru: {question}")
    print(f"{'='*80}\n")
    
    try:
        response = requests.post(
            FUNCTION_URL,
            headers=headers,
            json=payload,
            timeout=60  # RAG sorgusu biraz zaman alabilir
        )
        
        print(f" YANIT ALINDI:")
        print(f"Status Code: {response.status_code}")
        print(f"{'-'*80}")
        
        if response.status_code == 200:
            result = response.json()
            print(f" BAŞARILI!")
            print(f"\n CEVAP:")
            print(f"{result.get('answer', 'Cevap bulunamadı')}")
            print(f"\nKAYNAKLAR (İlk 500 karakter):")
            print(f"{result.get('sources', 'Kaynak bilgisi yok')}")
            return result
        else:
            print(f" HATA!")
            print(f"Hata Mesajı: {response.text}")
            return {"error": response.text}
            
    except requests.exceptions.Timeout:
        print(" İstek zaman aşımına uğradı (60 saniye)")
        return {"error": "timeout"}
    except requests.exceptions.ConnectionError:
        print(" Bağlantı hatası - URL'i kontrol edin")
        return {"error": "connection_error"}
    except Exception as e:
        print(f" Beklenmeyen hata: {str(e)}")
        return {"error": str(e)}


def main():
    """Test senaryolarını çalıştır"""
    
    # URL kontrolü
    if "<your-function-app>" in FUNCTION_URL:
        print("  UYARI: Lütfen FUNCTION_URL değişkenini Azure Portal'dan aldığınız gerçek URL ile değiştirin!")
        print("\nURL formatı:")
        print("https://your-function-app.azurewebsites.net/api/query?code=xxxxx\n")
        return
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   AZURE PRODUCTION RAG TEST                                ║
║                      Finance RAG - NVIDIA Test                             ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Test soruları
    test_questions = [
        "NVIDIA'nın son çeyrek geliri ne kadar?",
        "NVDA hissesi hakkında son haberlerde ne var?",
        "Fed faiz oranı trendi nasıl?",
        "NVIDIA'nın P/E ratio'su nedir?",
        "Yield curve durumu nasıl?"
    ]
    
    print(f"\n {len(test_questions)} test sorusu hazırlandı.\n")
    print("Hangi testi çalıştırmak istersiniz?")
    print("  1-5: Belirli bir soru")
    print("  A: Tüm soruları sırayla çalıştır")
    print("  Q: Kendi sorunu yaz")
    
    choice = input("\nSeçiminiz: ").strip().upper()
    
    if choice == 'A':
        for i, q in enumerate(test_questions, 1):
            print(f"\n[Test {i}/{len(test_questions)}]")
            test_query(q)
            input("\n Devam etmek için Enter'a basın...")
            
    elif choice == 'Q':
        custom_question = input("\n Sorunuzu yazın: ").strip()
        if custom_question:
            test_query(custom_question)
        else:
            print(" Boş soru gönderilemez!")
            
    elif choice.isdigit() and 1 <= int(choice) <= len(test_questions):
        idx = int(choice) - 1
        test_query(test_questions[idx])
    else:
        print(" Geçersiz seçim!")
    
    print("\n" + "="*80)
    print(" Test tamamlandı!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
