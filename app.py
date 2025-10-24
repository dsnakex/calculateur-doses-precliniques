import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Configuration de la page
st.set_page_config(
    page_title="Calculateur de doses",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .metric-box {
        background: linear-gradient(135deg, #0066cc 0%, #004499 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    .result-container {
        background: #f0f7ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #0066cc;
    }
</style>
""", unsafe_allow_html=True)

# Titre principal
st.title("🔬 Calculateur de doses")
st.markdown("### Études précliniques - Calcul des quantités de produits")

# Sidebar - Paramètres globaux
with st.sidebar:
    st.header("⚙️ Paramètres de l'étude")
    
    study_name = st.text_input("Nom de l'étude", value="Mon étude")
    
    st.markdown("---")
    st.subheader("Paramètres animaux")
    n_mice = st.slider("Souris par groupe", min_value=1, max_value=50, value=8, step=1)
    weight = st.slider("Poids moyen (g)", min_value=1, max_value=100, value=20, step=1)
    
    st.markdown("---")
    st.subheader("Durée du traitement")
    duration = st.slider("Durée (jours)", min_value=1, max_value=180, value=21, step=1)
    
    st.markdown("---")
    st.subheader("Marge de sécurité")
    margin = st.slider("Marge (%)", min_value=0, max_value=50, value=10, step=5)
    st.info("💡 Conseil: 10-20% pour compenser les pertes de préparation", icon="💡")

# Onglets principaux
tab1, tab2, tab3 = st.tabs(["📋 Groupes", "📊 Résultats", "ℹ️ Aide"])

with tab1:
    st.header("Configuration des groupes de traitement")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        n_groups = st.number_input("Nombre de groupes", min_value=1, max_value=20, value=5, step=1)
    
    with col2:
        if st.button("📝 Template: Anti-PD-1 + YK725", use_container_width=True):
            st.session_state.use_template = True
    
    st.markdown("---")
    
    # Créer les champs pour chaque groupe
    groups_data = []
    
    for i in range(n_groups):
        with st.expander(f"**Groupe {i+1}**", expanded=(i < 3)):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                name = st.text_input(
                    "Nom du groupe",
                    value=f"Groupe {i+1}",
                    key=f"name_{i}",
                    label_visibility="collapsed"
                )
            
            with col2:
                dose = st.number_input(
                    "Dose (mg/kg)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=0.0,
                    step=5.0,
                    key=f"dose_{i}",
                    label_visibility="collapsed"
                )
            
            with col3:
                dosing = st.selectbox(
                    "Dosing",
                    options=["QD (Quotidien)", "BID (2x/jour)"],
                    key=f"dosing_{i}",
                    label_visibility="collapsed"
                )
            
            groups_data.append({
                'name': name,
                'dose': dose,
                'dosing': dosing
            })
    
    # Bouton de calcul
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col2:
        calc_button = st.button("🧮 CALCULER", key="calc", use_container_width=True, type="primary")

with tab2:
    st.header("Résultats des calculs")
    
    if calc_button or 'results_df' in st.session_state:
        # Calcul
        wt_kg = weight / 1000
        results = []
        
        for idx, group in enumerate(groups_data, 1):
            dose = group['dose']
            dosing_label = group['dosing']
            dosing_freq = 1 if dosing_label == "QD (Quotidien)" else 0.5
            
            n_doses = duration / dosing_freq
            total_dose = dose * wt_kg * n_mice * n_doses
            total_dose_margin = total_dose * (1 + margin/100)
            
            results.append({
                'Groupe': f"G{idx}: {group['name']}",
                'Dose (mg/kg)': dose,
                'Dosing': dosing_label.split()[0],
                'Composé (mg)': round(total_dose, 2),
                f'Composé +{int(margin)}% (mg)': round(total_dose_margin, 2)
            })
        
        df = pd.DataFrame(results)
        st.session_state.results_df = df
        
        # Affichage des résultats
        st.markdown(f"### Résultats pour: **{study_name}**")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Métriques totales
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        total_col = f'Composé +{int(margin)}% (mg)'
        total_with_margin = df[total_col].sum()
        total_without_margin = df['Composé (mg)'].sum()
        
        with col1:
            st.markdown(f"""
            <div class="result-container">
                <div class="metric-label">Sans marge</div>
                <div class="metric-value">{round(total_without_margin, 1)} mg</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="result-container" style="background: linear-gradient(135deg, #00aa44 0%, #007733 100%); border-left-color: #00aa44;">
                <div class="metric-label">Avec marge (+{int(margin)}%)</div>
                <div class="metric-value">{round(total_with_margin, 1)} mg</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Export
        st.markdown("### 💾 Exporter les résultats")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name=f"doses_{study_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Doses')
            buffer.seek(0)
            
            st.download_button(
                label="📥 Télécharger Excel",
                data=buffer.getvalue(),
                file_name=f"doses_{study_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

with tab3:
    st.header("Guide d'utilisation")
    
    st.markdown("""
    ### 📖 Comment utiliser l'application
    
    **1. Paramètres globaux** (barre latérale gauche)
    - Indiquez le nom de votre étude
    - Définiez le nombre de souris par groupe
    - Spécifiez le poids moyen des animaux
    - Indiquez la durée totale du traitement
    - Ajustez la marge de sécurité (généralement 10-20%)
    
    **2. Configuration des groupes** (onglet "Groupes")
    - Définissez le nombre de groupes
    - Pour chaque groupe, entrez :
        - Le nom du groupe
        - La dose en mg/kg
        - La fréquence d'administration (QD ou BID)
    
    **3. Calcul** (onglet "Résultats")
    - Cliquez sur "CALCULER"
    - Consultez le tableau des résultats
    - Voyez les quantités totales à commander
    
    **4. Export**
    - Téléchargez en CSV (Excel, Google Sheets)
    - Ou en Excel (.xlsx)
    
    ### 🔤 Abréviations
    
    - **QD (Once Daily)** : 1 dose par jour
    - **BID (Twice Daily)** : 2 doses par jour
    
    ### 💡 Formule de calcul
    
    **Total = Dose (mg/kg) × Poids (kg) × Nombre d'animaux × Nombre de doses**
    
    Exemple pour QD : 20 jours → 20 doses  
    Exemple pour BID : 20 jours → 40 doses (2 par jour)
    
    ### ❓ Questions fréquentes
    
    **Q: Pourquoi ajouter une marge ?**  
    R: Pour compenser les pertes lors de la dilution, des seringues, et du pipetage.
    
    **Q: Comment savoir si j'ai assez de produit ?**  
    R: Utilisez la colonne "Composé +X% (mg)" pour être sûr d'avoir assez.
    
    **Q: Je peux modifier après le calcul ?**  
    R: Oui ! Modifiez les paramètres et recliquez sur "CALCULER".
    """)
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 12px;'>" +
        "Calculateur de doses v2.0 | Streamlit | © 2025" +
        "</div>",
        unsafe_allow_html=True
    )
