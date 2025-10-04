#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégration ExoMiner backend
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_exominer_endpoints():
    """Teste les endpoints ExoMiner"""
    
    print("🧪 Test des endpoints ExoMiner")
    print("=" * 50)
    
    # 1. Test de la liste des jobs (vide au début)
    print("1. Test GET /exominer/jobs")
    try:
        response = requests.get(f"{API_BASE_URL}/exominer/jobs")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Jobs récupérés: {data['total_jobs']}")
        else:
            print(f"❌ Erreur: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False
    
    # 2. Test d'upload d'un fichier CSV
    print("\n2. Test POST /exominer/analyze")
    
    # Créer un fichier CSV de test
    test_csv_content = """tic_id,sector_run
167526485,6-6
167526485,1-39"""
    
    files = {
        'file': ('test_tics.csv', test_csv_content, 'text/csv')
    }
    
    data = {
        'data_collection_mode': '2min',
        'num_processes': '1',
        'num_jobs': '1',
        'download_spoc_data_products': 'true',
        'stellar_parameters_source': 'ticv8',
        'ruwe_source': 'gaiadr2',
        'exominer_model': 'exominer++_single'
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/exominer/analyze", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analyse lancée: {result['job_id']}")
            job_id = result['job_id']
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur upload: {e}")
        return False
    
    # 3. Test du statut du job
    print(f"\n3. Test GET /exominer/jobs/{job_id}")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{API_BASE_URL}/exominer/jobs/{job_id}")
            if response.status_code == 200:
                job_status = response.json()
                print(f"   Tentative {attempt + 1}: Statut = {job_status['status']}, Progrès = {job_status.get('progress', 0)}%")
                
                if job_status['status'] == 'completed':
                    print("✅ Job terminé avec succès!")
                    break
                elif job_status['status'] == 'failed':
                    print(f"❌ Job échoué: {job_status.get('error', 'Erreur inconnue')}")
                    return False
                else:
                    time.sleep(5)  # Attendre 5 secondes avant le prochain check
            else:
                print(f"❌ Erreur statut: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ Erreur check statut: {e}")
            break
    else:
        print("⏰ Timeout - Job pas encore terminé après 50 secondes")
    
    # 4. Test des résultats (si job terminé)
    print(f"\n4. Test GET /exominer/jobs/{job_id}/results")
    try:
        response = requests.get(f"{API_BASE_URL}/exominer/jobs/{job_id}/results")
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Résultats récupérés: {results['results']['summary']}")
        else:
            print(f"❌ Erreur résultats: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur récupération résultats: {e}")
    
    # 5. Test de suppression du job
    print(f"\n5. Test DELETE /exominer/jobs/{job_id}")
    try:
        response = requests.delete(f"{API_BASE_URL}/exominer/jobs/{job_id}")
        if response.status_code == 200:
            print("✅ Job supprimé avec succès")
        else:
            print(f"❌ Erreur suppression: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur suppression: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Tests terminés!")
    return True

if __name__ == "__main__":
    test_exominer_endpoints()
