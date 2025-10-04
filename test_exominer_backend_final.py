#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégration ExoMiner backend
"""

import requests
import json
import time

def test_exominer_backend():
    """Test complet de l'intégration ExoMiner backend"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Test intégration ExoMiner backend")
    print("=" * 50)
    
    # Contenu CSV de test
    csv_content = """tic_id,sector_run
167526485,6-6
167526485,1-39"""
    
    # 1. Test upload et analyse
    print("1. Test upload CSV et lancement ExoMiner...")
    
    files = {
        'file': ('test_tics.csv', csv_content, 'text/csv')
    }
    
    data = {
        'data_collection_mode': '2min',
        'num_processes': 1,
        'num_jobs': 1,
        'download_spoc_data_products': 'true',
        'stellar_parameters_source': 'ticv8',
        'ruwe_source': 'gaiadr2',
        'exominer_model': 'exominer++_single'
    }
    
    try:
        response = requests.post(f"{base_url}/exominer/analyze", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analyse lancée avec succès")
            print(f"   Job ID: {result['job_id']}")
            print(f"   Succès: {result['success']}")
            
            job_id = result['job_id']
            
            # 2. Test polling du statut
            print("\n2. Test polling du statut...")
            
            max_attempts = 60  # 5 minutes max
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    status_response = requests.get(f"{base_url}/exominer/jobs/{job_id}")
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"   Statut: {status['status']} (progression: {status.get('progress', 0)}%)")
                        
                        if status['status'] == 'completed':
                            print("✅ Analyse terminée avec succès!")
                            break
                        elif status['status'] == 'failed':
                            print("❌ Analyse échouée")
                            if 'error' in status:
                                print(f"   Erreur: {status['error']}")
                            return False
                        
                        time.sleep(5)  # Attendre 5 secondes
                        attempt += 1
                    else:
                        print(f"❌ Erreur statut: {status_response.status_code}")
                        return False
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ Erreur requête: {e}")
                    return False
            
            if attempt >= max_attempts:
                print("⏰ Timeout - analyse trop longue")
                return False
            
            # 3. Test récupération des résultats
            print("\n3. Test récupération des résultats...")
            
            try:
                results_response = requests.get(f"{base_url}/exominer/jobs/{job_id}/results")
                
                if results_response.status_code == 200:
                    results = results_response.json()
                    print("✅ Résultats récupérés avec succès")
                    
                    if 'results' in results and 'summary' in results['results']:
                        summary = results['results']['summary']
                        print(f"   TICs analysés: {summary.get('total_tics_processed', 'N/A')}")
                        print(f"   Haute confiance: {summary.get('high_confidence_candidates', 'N/A')}")
                        print(f"   Score moyen: {summary.get('avg_score', 'N/A')}")
                    
                    # 4. Test téléchargement des résultats
                    print("\n4. Test téléchargement des résultats...")
                    
                    try:
                        download_response = requests.get(f"{base_url}/exominer/jobs/{job_id}/download")
                        
                        if download_response.status_code == 200:
                            print("✅ Téléchargement réussi")
                            print(f"   Taille: {len(download_response.content)} bytes")
                        else:
                            print(f"❌ Erreur téléchargement: {download_response.status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        print(f"❌ Erreur téléchargement: {e}")
                    
                    # 5. Test suppression du job
                    print("\n5. Test suppression du job...")
                    
                    try:
                        delete_response = requests.delete(f"{base_url}/exominer/jobs/{job_id}")
                        
                        if delete_response.status_code == 200:
                            print("✅ Job supprimé avec succès")
                        else:
                            print(f"❌ Erreur suppression: {delete_response.status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        print(f"❌ Erreur suppression: {e}")
                    
                    return True
                else:
                    print(f"❌ Erreur résultats: {results_response.status_code}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Erreur récupération résultats: {e}")
                return False
                
        else:
            print(f"❌ Erreur lancement analyse: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur connexion: {e}")
        return False

def test_jobs_list():
    """Test de la liste des jobs"""
    
    base_url = "http://localhost:8000"
    
    print("\n6. Test liste des jobs...")
    
    try:
        response = requests.get(f"{base_url}/exominer/jobs")
        
        if response.status_code == 200:
            jobs = response.json()
            print("✅ Liste des jobs récupérée")
            print(f"   Nombre de jobs: {jobs.get('total_jobs', 0)}")
            
            for job_id, job in jobs.get('jobs', {}).items():
                print(f"   - {job_id}: {job.get('status', 'unknown')}")
            
            return True
        else:
            print(f"❌ Erreur liste jobs: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur liste jobs: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Démarrage des tests ExoMiner backend")
    print("Assurez-vous que le backend est démarré sur http://localhost:8000")
    print()
    
    try:
        # Test principal
        success = test_exominer_backend()
        
        if success:
            # Test liste des jobs
            test_jobs_list()
            
            print("\n" + "=" * 50)
            print("🎉 TOUS LES TESTS SONT PASSÉS!")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("❌ TESTS ÉCHOUÉS!")
            print("=" * 50)
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
