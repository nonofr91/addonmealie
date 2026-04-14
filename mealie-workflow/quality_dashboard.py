#!/usr/bin/env python3
"""
QUALITY DASHBOARD WORKFLOW MEALIE
Dashboard de monitoring de la qualité en temps réel
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import argparse

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

from quality_checker import WorkflowQualityChecker

class QualityDashboard:
    """Dashboard de monitoring de la qualité du workflow Mealie"""
    
    def __init__(self):
        self.checker = WorkflowQualityChecker()
        self.reports_dir = Path(__file__).parent / "quality_reports"
        
    def display_current_quality(self) -> Dict:
        """Affiche la qualité actuelle du workflow"""
        print("🎯 DASHBOARD QUALITÉ WORKFLOW MEALIE")
        print("📊 État actuel de la qualité")
        print("=" * 80)
        
        # Fichiers à analyser
        scraped_file = "scraped_data/latest_scraped_recipes_mcp.json"
        structured_file = "structured_data/latest_mealie_structured_recipes.json"
        import_file = "import_reports/latest_mealie_import_report.json"
        
        # Vérifier si les fichiers existent
        missing_files = []
        for file_path in [scraped_file, structured_file, import_file]:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Fichiers manquants: {', '.join(missing_files)}")
            return {"status": "error", "missing_files": missing_files}
        
        # Lancer la vérification
        try:
            report = self.checker.run_complete_quality_check(scraped_file, structured_file, import_file)
            self.display_quality_summary(report)
            return report
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
            return {"status": "error", "error": str(e)}
    
    def display_quality_summary(self, report: Dict):
        """Affiche un résumé de la qualité"""
        score = report["global_score"]
        status = report["status"]
        level_scores = report["level_scores"]
        
        # Afficher le score global
        status_emoji = {
            "EXCELLENT": "🏆",
            "BON": "✅",
            "ACCEPTABLE": "⚠️",
            "INSUFFISANT": "❌"
        }
        
        print(f"\n{status_emoji.get(status, '❓')} SCORE GLOBAL: {score:.1f}/100 - {status}")
        print("─" * 80)
        
        # Scores par niveau
        print(f"📊 SCORES PAR NIVEAU:")
        print(f"   🔧 Structurel: {level_scores['structural']:.1f}/100")
        print(f"   📝 Contenu: {level_scores['content']:.1f}/100")
        print(f"   🎯 Métier: {level_scores['business']:.1f}/100")
        
        # Graphique simple
        self.display_score_graph(level_scores)
        
        # Problèmes critiques
        critical_issues = report.get("critical_issues", [])
        if critical_issues:
            print(f"\n🚨 PROBLÈMES CRITIQUES ({len(critical_issues)}):")
            for issue in critical_issues[:3]:  # Limiter à 3
                print(f"   ❌ {issue['issue']}")
        
        # Recommandations
        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMANDATIONS:")
            for rec in recommendations[:3]:  # Limiter à 3
                print(f"   {rec}")
    
    def display_score_graph(self, scores: Dict):
        """Affiche un graphique simple des scores"""
        print(f"\n📈 GRAPHIQUE DE QUALITÉ:")
        print("   " + "─" * 40)
        
        for level, score in scores.items():
            bar_length = int(score / 2.5)  # 40 caractères max pour 100%
            bar = "█" * bar_length + "░" * (40 - bar_length)
            
            level_emoji = {
                "structural": "🔧",
                "content": "📝", 
                "business": "🎯"
            }
            
            print(f"   {level_emoji.get(level, '📊')} {level:12} {bar} {score:.1f}")
        
        print("   " + "─" * 40)
    
    def display_historical_trends(self) -> Dict:
        """Affiche les tendances historiques"""
        print("\n📈 TENDANCES HISTORIQUES")
        print("=" * 50)
        
        if not self.reports_dir.exists():
            print("❌ Aucun rapport historique trouvé")
            return {"status": "no_data"}
        
        # Récupérer tous les rapports
        reports = []
        for file_path in self.reports_dir.glob("mealie_quality_report_*.json"):
            if file_path.name != "latest_mealie_quality_report.json":
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        reports.append({
                            "file": file_path.name,
                            "date": report.get("generated_at"),
                            "score": report.get("global_score", 0),
                            "status": report.get("status", "UNKNOWN")
                        })
                except Exception:
                    continue
        
        if not reports:
            print("❌ Aucune donnée historique disponible")
            return {"status": "no_data"}
        
        # Trier par date
        reports.sort(key=lambda x: x["date"])
        
        # Afficher les 5 derniers rapports
        print(f"📊 DERNIÈRES VÉRIFICATIONS:")
        for report in reports[-5:]:
            date_str = report["date"][:19].replace("T", " ")
            status_emoji = {
                "EXCELLENT": "🏆",
                "BON": "✅",
                "ACCEPTABLE": "⚠️",
                "INSUFFISANT": "❌"
            }
            
            emoji = status_emoji.get(report["status"], "❓")
            print(f"   {emoji} {date_str} | {report['score']:.1f}/100")
        
        # Calculer la tendance
        if len(reports) >= 2:
            recent_avg = sum(r["score"] for r in reports[-3:]) / min(3, len(reports))
            older_avg = sum(r["score"] for r in reports[-6:-3]) / min(3, len(reports) - 3) if len(reports) > 3 else recent_avg
            
            trend = "📈 Amélioration" if recent_avg > older_avg else "📉 Dégradation" if recent_avg < older_avg else "➡️ Stable"
            print(f"\n📊 TENDANCE: {trend} ({recent_avg:.1f} vs {older_avg:.1f})")
        
        return {"status": "success", "reports": reports}
    
    def display_detailed_analysis(self) -> Dict:
        """Affiche une analyse détaillée"""
        print("\n🔍 ANALYSE DÉTAILLÉE")
        print("=" * 50)
        
        # Récupérer le dernier rapport
        latest_report_path = self.reports_dir / "latest_mealie_quality_report.json"
        
        if not latest_report_path.exists():
            print("❌ Aucun rapport récent trouvé")
            return {"status": "no_data"}
        
        try:
            with open(latest_report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            detailed_results = report.get("detailed_results", {})
            
            # Analyse structurelle
            print("🔧 ANALYSE STRUCTURELLE:")
            structural = detailed_results.get("structural", {})
            for category, analysis in structural.items():
                if category != "overall_score" and isinstance(analysis, dict):
                    score = analysis.get("score", 0)
                    issues = analysis.get("issues", [])
                    status = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
                    print(f"   {status} {category.title()}: {score:.1f}/100")
                    for issue in issues[:2]:
                        print(f"      • {issue}")
            
            # Analyse contenu
            print("\n📝 ANALYSE CONTENU:")
            content = detailed_results.get("content", {})
            for category, analysis in content.items():
                if category != "overall_score" and isinstance(analysis, dict):
                    score = analysis.get("score", 0)
                    issues = analysis.get("issues", [])
                    status = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
                    print(f"   {status} {category.title()}: {score:.1f}/100")
                    for issue in issues[:2]:
                        print(f"      • {issue}")
            
            # Analyse métier
            print("\n🎯 ANALYSE MÉTIER:")
            business = detailed_results.get("business", {})
            for category, analysis in business.items():
                if category != "overall_score" and isinstance(analysis, dict):
                    score = analysis.get("score", 0)
                    issues = analysis.get("issues", [])
                    status = "✅" if score >= 90 else "⚠️" if score >= 70 else "❌"
                    print(f"   {status} {category.title()}: {score:.1f}/100")
                    for issue in issues[:2]:
                        print(f"      • {issue}")
            
            return {"status": "success", "report": report}
            
        except Exception as e:
            print(f"❌ Erreur lecture rapport: {e}")
            return {"status": "error", "error": str(e)}
    
    def display_action_plan(self) -> Dict:
        """Affiche le plan d'action"""
        print("\n🚀 PLAN D'ACTION")
        print("=" * 50)
        
        # Récupérer le dernier rapport
        latest_report_path = self.reports_dir / "latest_mealie_quality_report.json"
        
        if not latest_report_path.exists():
            print("❌ Aucun rapport récent trouvé")
            return {"status": "no_data"}
        
        try:
            with open(latest_report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            score = report.get("global_score", 0)
            status = report.get("status", "UNKNOWN")
            recommendations = report.get("recommendations", [])
            next_steps = report.get("next_steps", [])
            
            # État actuel
            status_messages = {
                "EXCELLENT": "🏆 Qualité excellente - Prêt pour la production",
                "BON": "✅ Qualité bonne - Améliorations mineures recommandées",
                "ACCEPTABLE": "⚠️ Qualité acceptable - Améliorations nécessaires",
                "INSUFFISANT": "❌ Qualité insuffisante - Corrections majeures requises"
            }
            
            print(f"📊 ÉTAT ACTUEL: {status_messages.get(status, '❓ État inconnu')}")
            print(f"🎯 SCORE: {score:.1f}/100")
            
            # Actions immédiates
            if score < 85:
                print(f"\n🔥 ACTIONS IMMÉDIATES:")
                priority = 1
                for rec in recommendations:
                    print(f"   {priority}. {rec}")
                    priority += 1
            
            # Prochaines étapes
            print(f"\n📋 PROCHAINES ÉTAPEs:")
            for i, step in enumerate(next_steps, 1):
                print(f"   {i}. {step}")
            
            # Validation checklist
            print(f"\n✅ CHECKLIST DE VALIDATION:")
            checklist_items = [
                ("Structure JSON valide", score >= 80),
                ("Format Mealie compatible", score >= 75),
                ("Pas de doublons critiques", score >= 70),
                ("Temps cohérents", score >= 70),
                ("Instructions utilisables", score >= 65),
                "Prêt pour agents MCP" if score >= 80 else "En cours pour agents MCP"
            ]
            
            for item, condition in checklist_items:
                if isinstance(condition, bool):
                    status = "✅" if condition else "❌"
                else:
                    status = condition
                print(f"   {status} {item}")
            
            return {"status": "success", "score": score, "ready_for_production": score >= 85}
            
        except Exception as e:
            print(f"❌ Erreur génération plan: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_dashboard(self, mode: str = "summary") -> Dict:
        """Lance le dashboard avec le mode spécifié"""
        modes = {
            "summary": self.display_current_quality,
            "trends": self.display_historical_trends,
            "detailed": self.display_detailed_analysis,
            "action": self.display_action_plan
        }
        
        if mode not in modes:
            print(f"❌ Mode inconnu: {mode}")
            print(f"📋 Modes disponibles: {', '.join(modes.keys())}")
            return {"status": "error", "error": "Mode inconnu"}
        
        return modes[mode]()
    
    def run_full_dashboard(self):
        """Lance le dashboard complet"""
        print("🎯 DASHBOARD COMPLET QUALITÉ WORKFLOW MEALIE")
        print("📊 Monitoring complet de la qualité")
        print("=" * 80)
        
        results = {}
        
        # 1. Qualité actuelle
        print("\n" + "="*80)
        results["current"] = self.display_current_quality()
        
        # 2. Tendances
        print("\n" + "="*80)
        results["trends"] = self.display_historical_trends()
        
        # 3. Analyse détaillée
        print("\n" + "="*80)
        results["detailed"] = self.display_detailed_analysis()
        
        # 4. Plan d'action
        print("\n" + "="*80)
        results["action"] = self.display_action_plan()
        
        # Résumé final
        print("\n" + "="*80)
        print("🎉 RÉSUMÉ DU DASHBOARD")
        
        current_score = results.get("current", {}).get("global_score", 0)
        current_status = results.get("current", {}).get("status", "UNKNOWN")
        ready_for_production = results.get("action", {}).get("ready_for_production", False)
        
        print(f"📊 Score actuel: {current_score:.1f}/100")
        print(f"🎯 Statut: {current_status}")
        print(f"🚀 Prêt pour production: {'✅ OUI' if ready_for_production else '❌ NON'}")
        
        return results

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Dashboard de qualité Workflow Mealie")
    parser.add_argument("--mode", choices=["summary", "trends", "detailed", "action", "full"], 
                       default="full", help="Mode d'affichage")
    
    args = parser.parse_args()
    
    dashboard = QualityDashboard()
    
    if args.mode == "full":
        dashboard.run_full_dashboard()
    else:
        dashboard.run_dashboard(args.mode)

if __name__ == "__main__":
    main()
