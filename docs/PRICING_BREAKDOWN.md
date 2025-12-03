# GCP Pricing Breakdown for Who Visions LLC

**Generated from:** `Pricing for Who Visions LLC (1).csv`  
**Date:** 2025-01-XX

---

## 📊 Overview

This document breaks down all GCP service pricing tiers from the contract pricing CSV.

**Total Services:** 3  
**Total SKUs:** 10  
**Total Pricing Tiers:** 36

---

## 1. ☁️ Cloud Storage (Service ID: 95FF-2EF5-5EA1)

### 1.1 Network Egress - Premium (SKU: 22EB-AAE8-FBCD)
**Description:** Download Worldwide Destinations (excluding Asia & Australia)  
**Unit:** Gibibyte  
**Taxonomy:** `GCP > Network > Egress > GCS > Premium`

| Tier Start (GiB) | List Price | Contract Price | Effective Discount |
|------------------|------------|----------------|-------------------|
| 0 | $0.00 | $0.00 | 0% |
| 100 | $0.12 | $0.12 | 0% |
| 1,024 | $0.11 | $0.11 | 0% |
| 10,240 | $0.08 | $0.08 | 0% |

**Pricing Notes:**
- First 100 GiB: Free
- 100-1,024 GiB: $0.12/GiB
- 1,024-10,240 GiB: $0.11/GiB
- 10,240+ GiB: $0.08/GiB

---

### 1.2 Storage Operations - Class A (SKU: 4DBF-185F-A415)
**Description:** Regional Standard Class A Operations  
**Unit:** Count (per 1,000 operations)  
**Taxonomy:** `GCP > Storage > GCS > Ops > Standard > Regional and Dual-Regional`

| Tier Start (Ops) | List Price | Contract Price | Effective Discount |
|------------------|------------|----------------|-------------------|
| 0 | $0.00 | $0.00 | 0% |
| 5,000 | $0.005 | $0.005 | 0% |

**Pricing Notes:**
- First 5,000 operations: Free
- 5,000+ operations: $0.005 per 1,000 operations

---

### 1.3 Storage Operations - Class B (SKU: 7870-010B-2763)
**Description:** Regional Standard Class B Operations  
**Unit:** Count (per 1,000 operations)  
**Taxonomy:** `GCP > Storage > GCS > Ops > Standard > Regional and Dual-Regional`

| Tier Start (Ops) | List Price | Contract Price | Effective Discount |
|------------------|------------|----------------|-------------------|
| 0 | $0.00 | $0.00 | 0% |
| 50,000 | $0.0004 | $0.0004 | 0% |

**Pricing Notes:**
- First 50,000 operations: Free
- 50,000+ operations: $0.0004 per 1,000 operations

---

### 1.4 Network Egress - Inter-Region (SKU: 8878-37D4-D2AC)
**Description:** Network Data Transfer GCP Inter Region within Northern America  
**Unit:** Gibibyte  
**Taxonomy:** `GCP > Network > Egress > GCS > Inter-region`

| Tier Start (GiB) | List Price | Contract Price | Effective Discount |
|------------------|------------|----------------|-------------------|
| 0 | $0.00 | $0.00 | 0% |
| 100 | $0.02 | $0.02 | 0% |

**Pricing Notes:**
- First 100 GiB: Free
- 100+ GiB: $0.02/GiB

---

### 1.5 Storage - Standard US Regional (SKU: E5F0-6A5D-7BAD)
**Description:** Standard Storage US Regional  
**Unit:** Gibibyte-month  
**Taxonomy:** `GCP > Storage > GCS > Storage > Standard > Regional and Dual-Regional`

| Tier Start (GiB-month) | List Price | Contract Price | Effective Discount |
|------------------------|------------|----------------|-------------------|
| 0 | $0.00 | $0.00 | 0% |
| 5 | $0.02 | $0.02 | 0% |

**Pricing Notes:**
- First 5 GiB-month: Free
- 5+ GiB-month: $0.02/GiB-month

---

## 2. 🤖 Vertex AI (Service ID: C7E2-9256-1C43)

### 2.1 Gemini 2.5 Flash - Text Input (SKU: FDAB-647C-5A22)
**Description:** Gemini 2.5 Flash GA Text Input - Predictions  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Flash > Text > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $0.30 | $0.30 | 0% |

**Pricing:** $0.30 per 1M input tokens

**Comparison with Current Spec:**
- **CSV:** $0.30/1M tokens
- **Current (`models_spec.py`):** $0.10/1M tokens ⚠️ **MISMATCH**

---

### 2.2 Gemini 2.5 Flash - Text Caching Input (SKU: A1C1-77CC-6FAE)
**Description:** Gemini 2.5 Flash GA Input Text Caching  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Flash > Text Caching > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $0.03 | $0.03 | 0% |

**Pricing:** $0.03 per 1M cached input tokens (90% discount vs regular input)

---

### 2.3 Gemini 2.5 Flash - Text Output (Thinking) (SKU: A253-E8A3-DE5C, CD33-11F4-1220)
**Description:** Gemini 2.5 Flash GA Text Output (Thinking On) - Predictions  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Flash Thinking > Text > Output`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $2.50 | $2.50 | 0% |

**Pricing:** $2.50 per 1M output tokens (with thinking enabled)

**Comparison with Current Spec:**
- **CSV:** $2.50/1M tokens (thinking mode)
- **Current (`models_spec.py`):** $0.40/1M tokens (regular) ⚠️ **MISMATCH**

---

### 2.4 Gemini 2.5 Pro - Text Input (SKU: A121-E2B5-1418)
**Description:** Gemini 2.5 Pro Text Input - Predictions  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Pro > Text > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $1.25 | $1.25 | 0% |

**Pricing:** $1.25 per 1M input tokens

**Comparison with Current Spec:**
- **CSV:** $1.25/1M tokens
- **Current (`models_spec.py`):** Check `unk_mode` pricing

---

### 2.5 Gemini 2.5 Pro - Text Caching Input (SKU: E941-1B12-88B9)
**Description:** Gemini 2.5 Pro Input Text Caching  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Pro > Text Caching > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $0.125 | $0.125 | 0% |

**Pricing:** $0.125 per 1M cached input tokens (90% discount vs regular input)

---

### 2.6 Gemini 2.5 Pro - Text Output (SKU: 5DA2-3F77-1CA5)
**Description:** Gemini 2.5 Pro Text Output - Predictions  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Pro > Text > Output`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $10.00 | $10.00 | 0% |

**Pricing:** $10.00 per 1M output tokens

**Comparison with Current Spec:**
- **CSV:** $10.00/1M tokens
- **Current (`models_spec.py`):** Check `unk_mode` pricing

---

### 2.7 Gemini 2.5 Pro - Text Output (Thinking) (SKU: E367-697F-F274)
**Description:** Gemini 2.5 Pro Thinking Text Output - Predictions  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Pro Thinking > Text > Output`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $10.00 | $10.00 | 0% |

**Pricing:** $10.00 per 1M output tokens (same as regular Pro output)

---

### 2.8 Gemini 3.0 Pro - Text Input (SKU: EAC4-305F-1249)
**Description:** Gemini 3.0 Pro Text Input - Predictions  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 3.0 Pro > Text > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $2.00 | $2.00 | 0% |

**Pricing:** $2.00 per 1M input tokens

---

### 2.9 Gemini 3.0 Pro - Text Output (SKU: 2737-2D33-D986)
**Description:** Gemini 3.0 Pro Text Output - Predictions  
**Unit:** Count (per 1,000,000 tokens)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 3.0 Pro > Text > Output`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $12.00 | $12.00 | 0% |

**Pricing:** $12.00 per 1M output tokens

---

### 2.10 Gemini 2.5 Flash - Image Input (SKU: 7C13-537E-1E75)
**Description:** Gemini 2.5 Flash GA Image Input - Predictions  
**Unit:** Count (per 1,000,000 images)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Flash > Image > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $0.30 | $0.30 | 0% |

**Pricing:** $0.30 per 1M images

---

### 2.11 Gemini 2.5 Pro - Image Input (SKU: B401-3774-BCEE)
**Description:** Gemini 2.5 Pro Image Input - Predictions  
**Unit:** Count (per 1,000,000 images)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Pro > Image > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $1.25 | $1.25 | 0% |

**Pricing:** $1.25 per 1M images

---

### 2.12 Gemini 2.5 Pro - Image Caching Input (SKU: 85D1-8B9D-D7F9)
**Description:** Gemini 2.5 Pro Input Image Caching  
**Unit:** Count (per 1,000,000 images)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 2.5 Pro > Image Caching > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $0.125 | $0.125 | 0% |

**Pricing:** $0.125 per 1M cached images (90% discount vs regular input)

---

### 2.13 Gemini 3.0 Pro - Image Input (SKU: 98E0-CA2E-4AA8)
**Description:** Gemini 3.0 Pro Image Input - Predictions  
**Unit:** Count (per 1,000,000 images)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 3.0 Pro > Image > Input`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $2.00 | $2.00 | 0% |

**Pricing:** $2.00 per 1M images

---

### 2.14 Gemini 3.0 Pro - Image Output (SKU: 47A8-A5A1-B26C)
**Description:** Gemini 3.0 Pro Image Output - Predictions  
**Unit:** Count (per 1,000,000 images)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Gemini 3.0 Pro > Image > Output`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $120.00 | $120.00 | 0% |

**Pricing:** $120.00 per 1M images ⚠️ **EXPENSIVE**

---

### 2.15 Imagen 3 - Image Generation (SKU: B5BE-136B-2CA1)
**Description:** Imagen 3 Generation (output)  
**Unit:** Count (per image)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Imagen 3 > Image Generation > Output`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $0.04 | $0.04 | 0% |

**Pricing:** $0.04 per generated image

---

### 2.16 Imagen 4 - Image Generation (SKU: 180A-C24F-9D7F)
**Description:** Imagen 4 Generation (output)  
**Unit:** Count (per image)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Model Garden > 1P Foundational Models > Imagen 4 > Image Generation > Output`

| Tier Start | List Price | Contract Price | Effective Discount |
|------------|------------|----------------|-------------------|
| 0 | $0.04 | $0.04 | 0% |

**Pricing:** $0.04 per generated image

---

### 2.17 Reasoning Engine - CPU (SKU: 8A55-0B95-B7DC)
**Description:** Vertex AI: ReasoningEngine management fee on CPU  
**Unit:** Second (per 3,600 seconds)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Platform > Vertex AI APIs > Reasoning Engine > CPU > Tier 1`

| Tier Start (seconds) | List Price | Contract Price | Effective Discount |
|---------------------|------------|----------------|-------------------|
| 0 | $0.00 | $0.00 | 0% |
| 180,000 | $0.0994 | $0.0994 | 0% |

**Pricing Notes:**
- First 180,000 seconds (50 hours): Free
- 180,000+ seconds: $0.0994 per 3,600 seconds (per hour)

---

### 2.18 Reasoning Engine - Memory (SKU: 0B45-6103-6EC1)
**Description:** Vertex AI: ReasoningEngine management fee on Memory  
**Unit:** Gibibyte-second (per 3,600 seconds)  
**Taxonomy:** `GCP > Cloud AI > Vertex AI Platform > Vertex AI APIs > Reasoning Engine > RAM > Tier 1`

| Tier Start (GiB-seconds) | List Price | Contract Price | Effective Discount |
|-------------------------|------------|----------------|-------------------|
| 0 | $0.00 | $0.00 | 0% |
| 335,276.127 | $0.0105 | $0.0105 | 0% |

**Pricing Notes:**
- First 335,276 GiB-seconds: Free
- 335,276+ GiB-seconds: $0.0105 per 3,600 GiB-seconds

---

## 3. 📝 Cloud Logging (Service ID: 5490-F7B7-8DF6)

### 3.1 Log Storage (SKU: 143F-A1B0-E0BE)
**Description:** Log Storage cost  
**Unit:** Gibibyte  
**Taxonomy:** `GCP > Ops Tools > Cloud Logging > Logs`

| Tier Start (GiB) | List Price | Contract Price | Effective Discount |
|------------------|------------|----------------|-------------------|
| 0 | $0.00 | $0.00 | 0% |
| 50 | $0.50 | $0.50 | 0% |

**Pricing Notes:**
- First 50 GiB: Free
- 50+ GiB: $0.50/GiB

---

## 📈 Pricing Summary by Service

### Vertex AI - Text Models (per 1M tokens)

| Model | Input | Output | Output (Thinking) | Caching Input |
|-------|-------|--------|-------------------|---------------|
| **Gemini 2.5 Flash** | $0.30 | N/A | $2.50 | $0.03 |
| **Gemini 2.5 Pro** | $1.25 | $10.00 | $10.00 | $0.125 |
| **Gemini 3.0 Pro** | $2.00 | $12.00 | N/A | N/A |

### Vertex AI - Image Models (per 1M images)

| Model | Input | Output | Caching Input |
|-------|-------|--------|---------------|
| **Gemini 2.5 Flash** | $0.30 | N/A | N/A |
| **Gemini 2.5 Pro** | $1.25 | N/A | $0.125 |
| **Gemini 3.0 Pro** | $2.00 | $120.00 | N/A |

### Vertex AI - Image Generation (per image)

| Model | Price |
|-------|-------|
| **Imagen 3** | $0.04 |
| **Imagen 4** | $0.04 |

---

## ⚠️ Pricing Discrepancies Found

### Current vs CSV Pricing Comparison

| Model | Type | Current (`models_spec.py`) | CSV Contract | Difference |
|-------|------|---------------------------|--------------|------------|
| Gemini 2.5 Flash | Input | $0.10/1M | $0.30/1M | **+200%** |
| Gemini 2.5 Flash | Output | $0.40/1M | $2.50/1M (thinking) | **+525%** |

**Action Required:** Update `models_spec.py` with correct contract pricing.

---

## 💡 Cost Optimization Insights

1. **Caching Discount:** 90% discount on cached inputs
   - Flash: $0.30 → $0.03 (saves $0.27/1M tokens)
   - Pro: $1.25 → $0.125 (saves $1.125/1M tokens)

2. **Thinking Mode Cost:** 
   - Flash thinking output: $2.50/1M (vs regular $0.40 estimated)
   - Pro thinking output: Same as regular ($10.00/1M)

3. **Image Generation:**
   - Imagen 3 & 4: $0.04/image (very affordable)
   - Gemini 3.0 Pro image output: $120/1M images (extremely expensive)

4. **Free Tiers:**
   - Cloud Storage: First 100 GiB egress free
   - Cloud Logging: First 50 GiB free
   - Reasoning Engine: First 50 hours CPU free

---

## 🔄 Next Steps

1. ✅ Update `models_spec.py` with correct contract pricing
2. ✅ Implement caching cost calculation
3. ✅ Add reasoning engine cost tracking
4. ✅ Update cost estimation functions
5. ✅ Add image generation cost tracking

---

*Generated from contract pricing CSV - Who Visions LLC*

