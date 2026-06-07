"""
OBERON-301 Risk-Based Data Quality Monitor v3
Core Scoring Engine - 6 Risk Dimensions, 10 Datasets
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class RiskScoringEngine:
    def __init__(self):
        self.demographics = None
        self.medical_history = None
        self.concomitant_meds = None
        self.adverse_events = None
        self.lab_data = None
        self.vital_signs = None
        self.disposition = None
        self.query_detail = None
        self.protocol_deviations = None
        self.visit_tracking = None
        self.all_subjects = set()
        self.results = {}
        self.study_avg_queries = 0

    def load_data(self, files_dict):
        for key in files_dict:
            df = pd.read_csv(files_dict[key])
            df.columns = df.columns.str.strip()
            setattr(self, key, df)
        self.all_subjects = set()
        for attr in ['demographics','medical_history','concomitant_meds','adverse_events','lab_data','vital_signs','disposition','query_detail','protocol_deviations','visit_tracking']:
            df = getattr(self, attr, None)
            if df is not None and 'Subject_ID' in df.columns:
                self.all_subjects.update(df['Subject_ID'].unique())
        if self.query_detail is not None:
            total_queries = len(self.query_detail)
            total_subjects = len(self.all_subjects)
            self.study_avg_queries = total_queries / total_subjects if total_subjects > 0 else 0

    def score_all_subjects(self):
        results = []
        for subject_id in sorted(self.all_subjects):
            scores = self._score_subject(subject_id)
            results.append(scores)
        self.results = results
        return results

    def _score_subject(self, subject_id):
        scores = {"Subject_ID": subject_id, "Site_ID": self._get_site(subject_id)}
        d1, d1d = self._score_completeness(subject_id)
        scores["D1_Completeness_Score"] = d1
        scores["D1_Details"] = d1d
        d2, d2d = self._score_query_rate(subject_id)
        scores["D2_QueryRate_Score"] = d2
        scores["D2_Details"] = d2d
        d3, d3d = self._score_temporal_anomalies(subject_id)
        scores["D3_Temporal_Score"] = d3
        scores["D3_Details"] = d3d
        d4, d4d = self._score_safety_signals(subject_id)
        scores["D4_Safety_Score"] = d4
        scores["D4_Details"] = d4d
        d5, d5d = self._score_site_risk(subject_id)
        scores["D5_SiteRisk_Score"] = d5
        scores["D5_Details"] = d5d
        d6, d6d = self._score_protocol_deviations(subject_id)
        scores["D6_ProtocolDev_Score"] = d6
        scores["D6_Details"] = d6d
        total = d1 + d2 + d3 + d4 + d5 + d6
        scores["Total_Risk_Score"] = total
        if total >= 61:
            scores["Risk_Category"] = "CRITICAL"
        elif total >= 41:
            scores["Risk_Category"] = "HIGH"
        elif total >= 21:
            scores["Risk_Category"] = "MEDIUM"
        else:
            scores["Risk_Category"] = "LOW"
        return scores

    def _get_site(self, subject_id):
        if self.demographics is not None:
            demo = self.demographics[self.demographics["Subject_ID"] == subject_id]
            if len(demo) > 0:
                return str(demo.iloc[0].get("Site_ID", "Unknown"))
        return "Unknown"

    # =============================================
    # D1: DATA COMPLETENESS (0-20)
    # =============================================
    def _score_completeness(self, subject_id):
        total_fields = 0
        missing_fields = 0
        details = []
        form_checks = [
            ("Demographics", self.demographics, ["DOB","Sex","Race","Screening_Date","Informed_Consent_Date"]),
            ("Medical_History", self.medical_history, ["MH_Term","MH_Start_Date","Ongoing_YN"]),
            ("Concomitant_Meds", self.concomitant_meds, ["Med_Name","Indication","Start_Date","Ongoing_YN"]),
            ("Adverse_Events", self.adverse_events, ["AE_Term","Severity","Seriousness","Causality","Start_Date","Action_Taken","Outcome"]),
            ("Lab_Data", self.lab_data, ["Visit_Name","Lab_Test","Result","Unit"]),
            ("Vital_Signs", self.vital_signs, ["BP_Systolic","BP_Diastolic","Weight_kg","Heart_Rate"]),
            ("Disposition", self.disposition, ["Status","Last_Visit_Date"]),
            ("Query_Detail", self.query_detail, ["Query_Type","Status","Open_Date"]),
            ("Protocol_Deviations", self.protocol_deviations, ["Category","Classification","CAPA_Status"]),
            ("Visit_Tracking", self.visit_tracking, ["Visit_Status","Expected_Date"]),
        ]
        for form_name, df, fields in form_checks:
            if df is None:
                continue
            subj_data = df[df["Subject_ID"] == subject_id]
            for _, row in subj_data.iterrows():
                for field in fields:
                    if field in row.index:
                        total_fields += 1
                        val = row[field]
                        if pd.isna(val) or str(val).strip() == "":
                            missing_fields += 1
                            if len(details) < 5:
                                details.append(f"Missing {field} in {form_name}")
        if total_fields == 0:
            return 20, ["No data found for subject"]
        missing_pct = (missing_fields / total_fields) * 100
        if missing_pct > 15:
            score = 20
        elif missing_pct > 10:
            score = 12
        elif missing_pct > 5:
            score = 5
        else:
            score = 0
        summary = f"{missing_fields}/{total_fields} fields missing ({missing_pct:.1f}%)"
        return score, [summary] + details[:5]

    # =============================================
    # D2: QUERY RATE (0-20) - Real Query Data
    # =============================================
    def _score_query_rate(self, subject_id):
        details = []
        if self.query_detail is None:
            return 0, ["No query data available"]
        subj_queries = self.query_detail[self.query_detail["Subject_ID"] == subject_id]
        total_queries = len(subj_queries)
        open_queries = len(subj_queries[subj_queries["Status"] == "Open"])
        answered_queries = len(subj_queries[subj_queries["Status"] == "Answered"])
        closed_queries = len(subj_queries[subj_queries["Status"] == "Closed"])
        # Calculate aging for open queries
        aged_queries = 0
        max_age = 0
        for _, q in subj_queries.iterrows():
            if q["Status"] == "Open":
                try:
                    age = int(q.get("Age_Days", 0))
                    if age > 14:
                        aged_queries += 1
                    if age > max_age:
                        max_age = age
                except (ValueError, TypeError):
                    pass
        issues = 0
        # High query volume
        if self.study_avg_queries > 0:
            ratio = total_queries / self.study_avg_queries
            if ratio > 3:
                issues += 4
                details.append(f"Query count ({total_queries}) is {ratio:.1f}x study average ({self.study_avg_queries:.1f})")
            elif ratio > 2:
                issues += 2
                details.append(f"Query count ({total_queries}) is {ratio:.1f}x study average")
        elif total_queries > 6:
            issues += 3
            details.append(f"High query volume: {total_queries} queries")
        # Open queries
        if open_queries >= 3:
            issues += 3
            details.append(f"{open_queries} queries still OPEN")
        elif open_queries >= 1:
            issues += 1
            details.append(f"{open_queries} query still OPEN")
        # Aged queries (>14 days)
        if aged_queries >= 2:
            issues += 3
            details.append(f"{aged_queries} queries aged >14 days (max age: {max_age} days)")
        elif aged_queries >= 1:
            issues += 1
            details.append(f"{aged_queries} query aged >14 days")
        # Answered but not closed
        if answered_queries >= 2:
            issues += 1
            details.append(f"{answered_queries} queries answered but not yet closed")
        if issues >= 8:
            score = 20
        elif issues >= 5:
            score = 15
        elif issues >= 3:
            score = 10
        elif issues >= 1:
            score = 5
        else:
            score = 0
        summary = f"{total_queries} queries (Open:{open_queries}, Answered:{answered_queries}, Closed:{closed_queries})"
        return score, [summary] + details[:5]

    # =============================================
    # D3: TEMPORAL ANOMALIES (0-15) - With Visit Tracking
    # =============================================
    def _score_temporal_anomalies(self, subject_id):
        issues = 0
        details = []
        # Date checks from demographics
        demo = self.demographics[self.demographics["Subject_ID"] == subject_id] if self.demographics is not None else pd.DataFrame()
        screening_date = None
        consent_date = None
        if len(demo) > 0:
            try:
                screening_date = pd.to_datetime(demo.iloc[0]["Screening_Date"])
                consent_date = pd.to_datetime(demo.iloc[0]["Informed_Consent_Date"])
            except (ValueError, TypeError):
                pass
        if screening_date and consent_date and consent_date > screening_date:
            issues += 2
            details.append(f"Consent ({consent_date.strftime('%Y-%m-%d')}) after Screening ({screening_date.strftime('%Y-%m-%d')})")
        # AE dates before consent
        if consent_date and self.adverse_events is not None:
            ae_data = self.adverse_events[self.adverse_events["Subject_ID"] == subject_id]
            for _, ae in ae_data.iterrows():
                try:
                    ae_start = pd.to_datetime(ae["Start_Date"])
                    if ae_start < consent_date:
                        issues += 2
                        details.append(f"AE '{ae['AE_Term']}' started before consent")
                except (ValueError, TypeError):
                    pass
        # MH start after screening
        if screening_date and self.medical_history is not None:
            mh_data = self.medical_history[self.medical_history["Subject_ID"] == subject_id]
            for _, mh in mh_data.iterrows():
                try:
                    mh_start = pd.to_datetime(mh["MH_Start_Date"])
                    if mh_start > screening_date:
                        issues += 2
                        details.append(f"MH '{mh['MH_Term']}' started after screening")
                except (ValueError, TypeError):
                    pass
        # Visit Tracking analysis
        if self.visit_tracking is not None:
            vt_data = self.visit_tracking[self.visit_tracking["Subject_ID"] == subject_id]
            # Missed visits
            missed = vt_data[vt_data["Visit_Status"] == "Missed"]
            if len(missed) >= 2:
                issues += 3
                details.append(f"{len(missed)} missed visits")
            elif len(missed) == 1:
                issues += 1
                details.append(f"1 missed visit: {missed.iloc[0]['Visit_Name']}")
            # Window violations
            outside_window = vt_data[vt_data["Within_Window"] == "No"]
            if len(outside_window) >= 2:
                issues += 2
                max_deviation = 0
                for _, v in outside_window.iterrows():
                    try:
                        dev = abs(int(v["Days_From_Expected"]))
                        if dev > max_deviation:
                            max_deviation = dev
                    except (ValueError, TypeError):
                        pass
                details.append(f"{len(outside_window)} visits outside window (max deviation: {max_deviation} days)")
            elif len(outside_window) == 1:
                issues += 1
                details.append(f"1 visit outside window: {outside_window.iloc[0]['Visit_Name']}")
        if issues >= 5:
            score = 15
        elif issues >= 3:
            score = 10
        elif issues >= 1:
            score = 5
        else:
            score = 0
        summary = f"{issues} temporal anomalies detected"
        return score, [summary] + details[:5]

    # =============================================
    # D4: SAFETY SIGNALS (0-20)
    # =============================================
    def _score_safety_signals(self, subject_id):
        issues = 0
        details = []
        ae_data = self.adverse_events[self.adverse_events["Subject_ID"] == subject_id] if self.adverse_events is not None else pd.DataFrame()
        ae_terms_lower = set(ae_data["AE_Term"].str.lower().tolist()) if len(ae_data) > 0 else set()
        has_any_ae = len(ae_data) > 0
        # Lab trending - ALT/AST
        if self.lab_data is not None:
            lab_data = self.lab_data[self.lab_data["Subject_ID"] == subject_id]
            out_of_range_count = 0
            for _, lab in lab_data.iterrows():
                try:
                    result = float(lab["Result"])
                    high = float(lab["Normal_Range_High"])
                    low = float(lab["Normal_Range_Low"])
                    if result > high * 3:
                        out_of_range_count += 1
                    elif result < low * 0.5:
                        out_of_range_count += 1
                except (ValueError, TypeError):
                    pass
            for test_name in ["ALT", "AST"]:
                test_data = lab_data[lab_data["Lab_Test"] == test_name].copy()
                if len(test_data) >= 3:
                    try:
                        test_data = test_data.copy()
                        test_data["Visit_Date_Parsed"] = pd.to_datetime(test_data["Visit_Date"])
                        test_data = test_data.sort_values("Visit_Date_Parsed")
                        values = test_data["Result"].astype(float).tolist()
                        high = float(test_data.iloc[0]["Normal_Range_High"])
                        if all(values[i] < values[i+1] for i in range(len(values)-1)):
                            if values[-1] > high * 2:
                                liver_terms = {"hepatotoxicity","liver","hepatic","alt","ast","transaminase"}
                                if not (ae_terms_lower & liver_terms):
                                    issues += 3
                                    details.append(f"{test_name} trending: {' > '.join(str(int(v)) for v in values)} (no liver AE)")
                    except (ValueError, TypeError):
                        pass
            # Hemoglobin dropping
            hgb_data = lab_data[lab_data["Lab_Test"] == "Hemoglobin"].copy()
            if len(hgb_data) >= 3:
                try:
                    hgb_data = hgb_data.copy()
                    hgb_data["Visit_Date_Parsed"] = pd.to_datetime(hgb_data["Visit_Date"])
                    hgb_data = hgb_data.sort_values("Visit_Date_Parsed")
                    values = hgb_data["Result"].astype(float).tolist()
                    low = float(hgb_data.iloc[0]["Normal_Range_Low"])
                    if values[-1] < low and (values[0] - values[-1]) > 3:
                        anemia_terms = {"anemia","anaemia","hemoglobin"}
                        if not (ae_terms_lower & anemia_terms):
                            issues += 3
                            details.append(f"Hemoglobin dropping: {' > '.join(str(v) for v in values)} (no AE)")
                except (ValueError, TypeError):
                    pass
            # Abnormal labs but zero AEs
            if out_of_range_count >= 3 and not has_any_ae:
                issues += 3
                details.append(f"{out_of_range_count} out-of-range labs but ZERO AEs reported")
        # Vital signs - BP
        if self.vital_signs is not None:
            vs_data = self.vital_signs[self.vital_signs["Subject_ID"] == subject_id]
            if len(vs_data) >= 3:
                try:
                    high_bp = sum(1 for _, vs in vs_data.iterrows() if float(vs["BP_Systolic"]) > 160 or float(vs["BP_Diastolic"]) > 100)
                    if high_bp >= 3:
                        if not (ae_terms_lower & {"hypertension","blood pressure"}):
                            issues += 2
                            details.append(f"BP elevated at {high_bp} visits, no hypertension AE")
                except (ValueError, TypeError):
                    pass
            # Weight change
            if len(vs_data) >= 2:
                try:
                    vs_sorted = vs_data.copy()
                    vs_sorted["Visit_Date_Parsed"] = pd.to_datetime(vs_sorted["Visit_Date"])
                    vs_sorted = vs_sorted.sort_values("Visit_Date_Parsed")
                    weights = vs_sorted["Weight_kg"].astype(float).tolist()
                    for i in range(1, len(weights)):
                        if abs(weights[i] - weights[i-1]) > 7:
                            issues += 2
                            details.append(f"Weight change {weights[i-1]}kg > {weights[i]}kg")
                            break
                except (ValueError, TypeError):
                    pass
        if issues >= 6:
            score = 20
        elif issues >= 4:
            score = 15
        elif issues >= 2:
            score = 10
        elif issues >= 1:
            score = 5
        else:
            score = 0
        summary = f"{issues} safety signal indicators"
        return score, [summary] + details[:5]

    # =============================================
    # D5: SITE RISK (0-15) - With Query Data
    # =============================================
    def _score_site_risk(self, subject_id):
        site_id = self._get_site(subject_id)
        if site_id == "Unknown":
            return 8, ["No site information"]
        if self.demographics is None:
            return 0, ["No demographics data"]
        site_subjects = self.demographics[self.demographics["Site_ID"] == site_id]["Subject_ID"].tolist()
        if len(site_subjects) < 2:
            return 0, ["Single subject at site"]
        details = []
        issues = 0
        # Site query metrics
        if self.query_detail is not None:
            site_queries = self.query_detail[self.query_detail["Site_ID"] == site_id]
            site_open = len(site_queries[site_queries["Status"] == "Open"])
            site_total = len(site_queries)
            queries_per_subject = site_total / len(site_subjects) if len(site_subjects) > 0 else 0
            if queries_per_subject > self.study_avg_queries * 1.5 and self.study_avg_queries > 0:
                issues += 2
                details.append(f"Site query rate ({queries_per_subject:.1f}/subj) is {queries_per_subject/self.study_avg_queries:.1f}x study avg")
            if site_open >= 5:
                issues += 2
                details.append(f"Site has {site_open} open queries")
            # Aged queries at site
            aged_at_site = 0
            for _, q in site_queries.iterrows():
                if q["Status"] == "Open":
                    try:
                        if int(q.get("Age_Days", 0)) > 14:
                            aged_at_site += 1
                    except (ValueError, TypeError):
                        pass
            if aged_at_site >= 3:
                issues += 1
                details.append(f"{aged_at_site} aged queries (>14 days) at site")
        # Site AE reporting rate
        if self.adverse_events is not None:
            study_ae_rate = len(self.adverse_events) / len(self.all_subjects) if len(self.all_subjects) > 0 else 0
            site_ae_count = len(self.adverse_events[self.adverse_events["Subject_ID"].isin(site_subjects)])
            site_ae_rate = site_ae_count / len(site_subjects) if len(site_subjects) > 0 else 0
            if site_ae_rate < study_ae_rate * 0.5 and study_ae_rate > 0:
                issues += 2
                details.append(f"Site AE rate ({site_ae_rate:.1f}) below study avg ({study_ae_rate:.1f})")
        # Site PD rate
        if self.protocol_deviations is not None:
            site_pds = self.protocol_deviations[self.protocol_deviations["Subject_ID"].isin(site_subjects)]
            site_major_pds = len(site_pds[site_pds["Classification"] == "Major"])
            if site_major_pds >= 3:
                issues += 2
                details.append(f"Site has {site_major_pds} major protocol deviations")
        # Site discontinuation rate
        if self.disposition is not None:
            site_disp = self.disposition[self.disposition["Subject_ID"].isin(site_subjects)]
            disc_count = len(site_disp[site_disp["Status"] == "Discontinued"])
            disc_rate = disc_count / len(site_subjects) * 100
            if disc_rate > 30:
                issues += 1
                details.append(f"Site discontinuation rate: {disc_rate:.0f}%")
        if issues >= 5:
            score = 15
        elif issues >= 3:
            score = 10
        elif issues >= 1:
            score = 5
        else:
            score = 0
        summary = f"Site {site_id}: {len(site_subjects)} subjects, {issues} risk indicators"
        return score, [summary] + details[:5]

    # =============================================
    # D6: PROTOCOL DEVIATIONS (0-10) - With PD Data
    # =============================================
    def _score_protocol_deviations(self, subject_id):
        issues = 0
        details = []
        # Age check
        if self.demographics is not None:
            demo = self.demographics[self.demographics["Subject_ID"] == subject_id]
            if len(demo) > 0:
                try:
                    dob = pd.to_datetime(demo.iloc[0]["DOB"])
                    screening = pd.to_datetime(demo.iloc[0]["Screening_Date"])
                    age = (screening - dob).days / 365.25
                    if age < 18 or age > 75:
                        issues += 2
                        details.append(f"Age {age:.0f} outside inclusion criteria (18-75)")
                except (ValueError, TypeError):
                    pass
        # Exclusion terms in MH
        if self.medical_history is not None:
            exclusion_terms = ["hepatic impairment","liver failure","cirrhosis","severe renal impairment","dialysis","active malignancy"]
            mh_data = self.medical_history[self.medical_history["Subject_ID"] == subject_id]
            for _, mh in mh_data.iterrows():
                mh_term = str(mh.get("MH_Term", "")).lower()
                for excl in exclusion_terms:
                    if excl in mh_term:
                        issues += 2
                        details.append(f"Exclusion: '{mh['MH_Term']}' in Medical History")
                        break
        # Protocol Deviation records
        if self.protocol_deviations is not None:
            pd_data = self.protocol_deviations[self.protocol_deviations["Subject_ID"] == subject_id]
            total_pds = len(pd_data)
            major_pds = len(pd_data[pd_data["Classification"] == "Major"])
            open_capa = len(pd_data[pd_data["CAPA_Status"] == "Open"])
            in_progress_capa = len(pd_data[pd_data["CAPA_Status"] == "In Progress"])
            if major_pds >= 2:
                issues += 3
                details.append(f"{major_pds} major protocol deviations")
            elif major_pds == 1:
                issues += 1
                details.append(f"1 major protocol deviation")
            if total_pds >= 3:
                issues += 1
                details.append(f"{total_pds} total protocol deviations")
            if open_capa >= 1:
                issues += 2
                details.append(f"{open_capa} open CAPA(s) requiring resolution")
            if in_progress_capa >= 1:
                issues += 1
                details.append(f"{in_progress_capa} CAPA(s) in progress")
            # List PD categories
            if total_pds > 0:
                categories = pd_data["Category"].value_counts().head(3)
                for cat, count in categories.items():
                    details.append(f"PD: {cat} (x{count})")
        # Fatal AE vs disposition check
        if self.adverse_events is not None and self.disposition is not None:
            ae_data = self.adverse_events[self.adverse_events["Subject_ID"] == subject_id]
            has_fatal = any(str(ae.get("Outcome", "")).strip() == "Fatal" for _, ae in ae_data.iterrows())
            if has_fatal:
                disp = self.disposition[self.disposition["Subject_ID"] == subject_id]
                if len(disp) > 0:
                    status = str(disp.iloc[0].get("Status", "")).strip()
                    reason = str(disp.iloc[0].get("Reason_Discontinuation", "")).strip()
                    if status == "Completed":
                        issues += 2
                        details.append(f"Fatal AE but disposition: Completed")
                    elif status == "Discontinued" and reason != "Death":
                        issues += 1
                        details.append(f"Fatal AE but reason: {reason} (not Death)")
        # Completed but too short
        if self.disposition is not None and self.demographics is not None:
            disp = self.disposition[self.disposition["Subject_ID"] == subject_id]
            demo = self.demographics[self.demographics["Subject_ID"] == subject_id]
            if len(disp) > 0 and len(demo) > 0:
                try:
                    if str(disp.iloc[0].get("Status", "")).strip() == "Completed":
                        screening = pd.to_datetime(demo.iloc[0]["Screening_Date"])
                        last_visit = pd.to_datetime(disp.iloc[0]["Last_Visit_Date"])
                        duration = (last_visit - screening).days
                        if duration < 56:
                            issues += 2
                            details.append(f"Completed in {duration} days (expected ~112)")
                except (ValueError, TypeError):
                    pass
        if issues >= 6:
            score = 10
        elif issues >= 4:
            score = 8
        elif issues >= 2:
            score = 5
        elif issues >= 1:
            score = 3
        else:
            score = 0
        summary = f"{issues} protocol deviation indicators"
        return score, [summary] + details[:7]

    # =============================================
    # REPORTS
    # =============================================
    def get_summary(self):
        if not self.results:
            return {}
        df = pd.DataFrame(self.results)
        categories = df["Risk_Category"].value_counts().to_dict()
        top_subjects = df.nlargest(10, "Total_Risk_Score")[["Subject_ID","Site_ID","Total_Risk_Score","Risk_Category","D1_Completeness_Score","D2_QueryRate_Score","D3_Temporal_Score","D4_Safety_Score","D5_SiteRisk_Score","D6_ProtocolDev_Score"]].to_dict("records")
        site_scores = df.groupby("Site_ID")["Total_Risk_Score"].agg(["mean","max","count"]).reset_index()
        site_scores.columns = ["Site_ID","Avg_Score","Max_Score","Subject_Count"]
        site_scores = site_scores.sort_values("Avg_Score", ascending=False).to_dict("records")
        dimension_avgs = {
            "D1_Completeness": df["D1_Completeness_Score"].mean(),
            "D2_QueryRate": df["D2_QueryRate_Score"].mean(),
            "D3_Temporal": df["D3_Temporal_Score"].mean(),
            "D4_Safety": df["D4_Safety_Score"].mean(),
            "D5_SiteRisk": df["D5_SiteRisk_Score"].mean(),
            "D6_ProtocolDev": df["D6_ProtocolDev_Score"].mean(),
        }
        # Query summary
        query_summary = {}
        if self.query_detail is not None:
            query_summary = {
                "total_queries": len(self.query_detail),
                "open_queries": len(self.query_detail[self.query_detail["Status"] == "Open"]),
                "avg_per_subject": round(self.study_avg_queries, 1),
            }
        # PD summary
        pd_summary = {}
        if self.protocol_deviations is not None:
            pd_summary = {
                "total_pds": len(self.protocol_deviations),
                "major_pds": len(self.protocol_deviations[self.protocol_deviations["Classification"] == "Major"]),
                "open_capas": len(self.protocol_deviations[self.protocol_deviations["CAPA_Status"] == "Open"]),
            }
        # Visit summary
        visit_summary = {}
        if self.visit_tracking is not None:
            visit_summary = {
                "total_visits": len(self.visit_tracking),
                "missed_visits": len(self.visit_tracking[self.visit_tracking["Visit_Status"] == "Missed"]),
                "window_violations": len(self.visit_tracking[self.visit_tracking["Within_Window"] == "No"]),
            }
        return {
            "total_subjects": len(df),
            "categories": categories,
            "top_subjects": top_subjects,
            "site_summary": site_scores,
            "avg_score": round(df["Total_Risk_Score"].mean(), 1),
            "max_score": int(df["Total_Risk_Score"].max()),
            "min_score": int(df["Total_Risk_Score"].min()),
            "dimension_averages": {k: round(v, 1) for k, v in dimension_avgs.items()},
            "query_summary": query_summary,
            "pd_summary": pd_summary,
            "visit_summary": visit_summary,
        }

    def get_subject_detail(self, subject_id):
        for r in self.results:
            if r["Subject_ID"] == subject_id:
                return r
        return None

    def export_to_csv(self):
        if not self.results:
            return pd.DataFrame()
        export_rows = []
        for r in self.results:
            export_rows.append({
                "Subject_ID": r["Subject_ID"], "Site_ID": r["Site_ID"],
                "Total_Risk_Score": r["Total_Risk_Score"], "Risk_Category": r["Risk_Category"],
                "D1_Completeness": r["D1_Completeness_Score"], "D2_QueryRate": r["D2_QueryRate_Score"],
                "D3_Temporal": r["D3_Temporal_Score"], "D4_Safety": r["D4_Safety_Score"],
                "D5_SiteRisk": r["D5_SiteRisk_Score"], "D6_ProtocolDev": r["D6_ProtocolDev_Score"],
                "D1_Details": "; ".join(r["D1_Details"][:3]), "D2_Details": "; ".join(r["D2_Details"][:3]),
                "D3_Details": "; ".join(r["D3_Details"][:3]), "D4_Details": "; ".join(r["D4_Details"][:3]),
                "D5_Details": "; ".join(r["D5_Details"][:3]), "D6_Details": "; ".join(r["D6_Details"][:3]),
            })
        return pd.DataFrame(export_rows)
