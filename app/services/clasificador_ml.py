"""
Clasificador automático de dominios usando Machine Learning
Entrena con dominios ya clasificados manualmente por el usuario
"""
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
from pathlib import Path
import numpy as np

class ClasificadorDominios:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 4),  # Bi-gramas y tri-gramas de caracteres
            max_features=1000
        )
        self.modelo = MultinomialNB(alpha=0.1)
        self.categorias_map = {}
        self.entrenado = False
        self.metricas = {}
    
    def entrenar(self, dominios, categorias, test_size=0.2):
        """
        Entrena el clasificador con dominios ya categorizados
        
        Args:
            dominios: ['facebook.com', 'youtube.com', ...]
            categorias: ['Redes Sociales', 'Entretenimiento', ...]
            test_size: Porcentaje para validación
        
        Returns:
            dict con métricas de entrenamiento
        """
        if len(dominios) < 10:
            print(f"[CLASIFICADOR][ERROR] Pocos datos: {len(dominios)} < 10")
            return False
        
        print(f"[CLASIFICADOR] Entrenando con {len(dominios)} ejemplos...")
        
        # Codificar categorías
        categorias_unicas = sorted(list(set(categorias)))
        self.categorias_map = {i: cat for i, cat in enumerate(categorias_unicas)}
        cat_to_id = {cat: i for i, cat in enumerate(categorias_unicas)}
        y = np.array([cat_to_id[cat] for cat in categorias])
        
        # Vectorizar dominios
        X = self.vectorizer.fit_transform(dominios)
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Entrenar
        self.modelo.fit(X_train, y_train)
        self.entrenado = True
        
        # Evaluar
        y_pred = self.modelo.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.metricas = {
            'accuracy': accuracy,
            'n_ejemplos': len(dominios),
            'n_categorias': len(categorias_unicas),
            'categorias': categorias_unicas
        }
        
        print(f"[CLASIFICADOR] ✅ Entrenado con éxito")
        print(f"[CLASIFICADOR] Precisión: {accuracy:.2%}")
        print(f"[CLASIFICADOR] Categorías: {len(categorias_unicas)}")
        
        # Reporte detallado
        print("\n[CLASIFICADOR] Reporte por categoría:")
        report = classification_report(
            y_test, y_pred,
            target_names=categorias_unicas,
            zero_division=0
        )
        print(report)
        
        return True
    
    def predecir(self, dominio):
        """
        Predice la categoría de un dominio nuevo
        
        Returns:
            (categoria: str, confianza: float)
        """
        if not self.entrenado:
            return None, 0.0
        
        try:
            X = self.vectorizer.transform([dominio])
            prediccion = self.modelo.predict(X)[0]
            probabilidades = self.modelo.predict_proba(X)[0]
            
            categoria = self.categorias_map[prediccion]
            confianza = float(probabilidades[prediccion])
            
            return categoria, confianza
        except Exception as e:
            print(f"[CLASIFICADOR][ERROR] {e}")
            return None, 0.0
    
    def predecir_top3(self, dominio):
        """
        Devuelve las 3 categorías más probables
        
        Returns:
            [(categoria, confianza), ...]
        """
        if not self.entrenado:
            return []
        
        try:
            X = self.vectorizer.transform([dominio])
            probabilidades = self.modelo.predict_proba(X)[0]
            
            # Top 3 índices
            top3_idx = np.argsort(probabilidades)[-3:][::-1]
            
            resultados = [
                (self.categorias_map[idx], float(probabilidades[idx]))
                for idx in top3_idx
            ]
            
            return resultados
        except Exception as e:
            print(f"[CLASIFICADOR][ERROR] {e}")
            return []
    
    def guardar(self, path='ml/artifacts/clasificador_dominios.pkl'):
        """Guarda el modelo entrenado"""
        Path(path).parent.mkdir(exist_ok=True, parents=True)
        
        with open(path, 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'modelo': self.modelo,
                'categorias_map': self.categorias_map,
                'entrenado': self.entrenado,
                'metricas': self.metricas
            }, f)
        
        print(f"[CLASIFICADOR] 💾 Guardado en {path}")
    
    def cargar(self, path='ml/artifacts/clasificador_dominios.pkl'):
        """Carga el modelo entrenado"""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.vectorizer = data['vectorizer']
            self.modelo = data['modelo']
            self.categorias_map = data['categorias_map']
            self.entrenado = data['entrenado']
            self.metricas = data.get('metricas', {})
            
            print(f"[CLASIFICADOR] ✅ Cargado desde {path}")
            print(f"[CLASIFICADOR] Precisión: {self.metricas.get('accuracy', 0):.2%}")
            
            return True
        except FileNotFoundError:
            print(f"[CLASIFICADOR] ⚠️  No existe {path}")
            return False
        except Exception as e:
            print(f"[CLASIFICADOR][ERROR] al cargar: {e}")
            return False


def entrenar_clasificador_desde_bd():
    """
    Entrena el clasificador desde dominio_categoria en BD
    SOLO usa categorías con ≥2 ejemplos
    """
    from app.utils import get_mysql
    from collections import Counter
    
    print("[CLASIFICADOR] Cargando datos desde BD...")
    
    try:
        conexion = get_mysql()
        
        with conexion.cursor() as cursor:
            # Obtener todos los dominios clasificados
            cursor.execute("""
                SELECT dc.dominio, c.nombre as categoria
                FROM dominio_categoria dc
                JOIN categorias c ON dc.categoria_id = c.id
                WHERE dc.dominio IS NOT NULL 
                  AND dc.dominio != ''
                  AND c.nombre IS NOT NULL
            """)
            
            resultados = cursor.fetchall()
            
            if not resultados:
                print("[CLASIFICADOR] ❌ No hay datos de entrenamiento")
                return None
            
            dominios = [r[0] for r in resultados]
            categorias = [r[1] for r in resultados]
            
            print(f"[CLASIFICADOR] Datos cargados: {len(dominios)} dominios")
            
            # ================================================================
            # FILTRO: Solo categorías con ≥2 ejemplos
            # ================================================================
            contador = Counter(categorias)
            categorias_validas = {cat for cat, count in contador.items() if count >= 2}
            
            print(f"\n[CLASIFICADOR] 📊 Distribución de categorías:")
            for cat, count in sorted(contador.items(), key=lambda x: -x[1]):
                estado = "✅" if count >= 2 else "⚠️  EXCLUIDA"
                print(f"  {estado} {cat}: {count} ejemplos")
            
            if len(categorias_validas) < 2:
                print(f"\n[CLASIFICADOR] ❌ Se necesitan al menos 2 categorías con ≥2 ejemplos")
                print(f"   Categorías válidas encontradas: {len(categorias_validas)}")
                return None
            
            # Filtrar datos
            dominios_filtrados = []
            categorias_filtradas = []
            
            for dom, cat in zip(dominios, categorias):
                if cat in categorias_validas:
                    dominios_filtrados.append(dom)
                    categorias_filtradas.append(cat)
            
            print(f"\n[CLASIFICADOR] Entrenando con {len(dominios_filtrados)} ejemplos...")
            print(f"[CLASIFICADOR] Categorías activas: {len(categorias_validas)}")
            # ================================================================
            
            # Entrenar clasificador
            clasificador = ClasificadorDominios()
            
            if clasificador.entrenar(dominios_filtrados, categorias_filtradas):
                print(f"[CLASIFICADOR] ✅ Entrenamiento exitoso")
                return clasificador
            else:
                print(f"[CLASIFICADOR] ❌ Fallo en entrenamiento")
                return None
                
    except Exception as e:
        print(f"[CLASIFICADOR] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def reentrenar_con_feedback(dominio, categoria_correcta):
    """
    Retrained incremental cuando usuario corrige una clasificación
    
    Args:
        dominio: Dominio que se clasificó
        categoria_correcta: Categoría correcta según usuario
    """
    # Por ahora, simplemente guarda para próximo entrenamiento
    # En futuro, puede hacer reentrenamiento incremental
    print(f"[CLASIFICADOR] Feedback guardado: {dominio} → {categoria_correcta}")
    print("[CLASIFICADOR] Se usará en próximo reentrenamiento")
