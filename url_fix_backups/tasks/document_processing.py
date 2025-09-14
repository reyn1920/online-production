# tasks / document_processing.py - Automated document and presentation generation

import base64
import json
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import markdown
import requests
import yaml
from celery import Task
from jinja2 import Environment, FileSystemLoader, Template
from PIL import Image, ImageDraw, ImageFont

from celery_app import celery_app

logger = logging.getLogger(__name__)


class DocumentProcessingTask(Task):
    """Base class for document processing tasks with retry logic"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_jitter = False

@celery_app.task(base = DocumentProcessingTask, bind = True)


def generate_product_documentation(
    self, product_data: Dict[str, Any], output_formats: List[str] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive product documentation in multiple formats

    Args:
        product_data: Product information and specifications
        output_formats: List of desired output formats (pdf, html, docx, epub)

    Returns:
        Dict containing generated document paths and metadata
    """
    try:
        logger.info(
            f"Generating product documentation for {product_data.get('name', 'Unknown Product')}"
        )

        if output_formats is None:
            output_formats = ["pdf", "html"]

        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Generate markdown content from product data
            markdown_content = generate_product_markdown(product_data)

            # Write markdown file
            markdown_file = temp_path / "product_documentation.md"
            with open(markdown_file, "w", encoding="utf - 8") as f:
                f.write(markdown_content)

            # Generate documents in requested formats
            generated_files = {}

            for format_type in output_formats:
                try:
                    output_file = generate_document_format(
                        markdown_file, format_type, temp_path, product_data
                    )

                    if output_file and output_file.exists():
                        # Move to permanent location
                        permanent_path = save_generated_document(
                            output_file, product_data.get("id", "unknown"), format_type
                        )
                        generated_files[format_type] = str(permanent_path)

                except Exception as e:
                    logger.error(f"Failed to generate {format_type} format: {str(e)}")
                    generated_files[format_type] = {"error": str(e)}

            logger.info(f"Product documentation generation completed")
            return {
                "status": "success",
                    "product_id": product_data.get("id"),
                    "product_name": product_data.get("name"),
                    "generated_files": generated_files,
                    "formats_requested": output_formats,
                    "formats_generated": [
                    f
                    for f in generated_files.keys()
                    if "error" not in str(generated_files[f])
                ],
                    "generated_at": datetime.utcnow().isoformat(),
                    }

    except Exception as e:
        logger.error(f"Product documentation generation failed: {str(e)}")
        raise self.retry(exc = e)

@celery_app.task(base = DocumentProcessingTask, bind = True)


def create_marketing_presentation(
    self, business_data: Dict[str, Any], presentation_type: str = "pitch"
) -> Dict[str, Any]:
    """
    Create marketing presentations using Marp

    Args:
        business_data: Business information and marketing content
        presentation_type: Type of presentation (pitch, product, training, report)

    Returns:
        Dict containing presentation files and metadata
    """
    try:
        logger.info(
            f"Creating {presentation_type} presentation for {business_data.get('name', 'Unknown Business')}"
        )

        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Generate Marp markdown content
            marp_content = generate_marp_presentation(business_data, presentation_type)

            # Write Marp markdown file
            marp_file = temp_path / f"{presentation_type}_presentation.md"
            with open(marp_file, "w", encoding="utf - 8") as f:
                f.write(marp_content)

            # Generate presentation formats
            generated_files = {}

            # Generate HTML presentation
            html_file = generate_marp_html(marp_file, temp_path)
            if html_file and html_file.exists():
                permanent_html = save_generated_document(
                    html_file,
                        f"{business_data.get('id', 'unknown')}_{presentation_type}",
                        "html",
                        )
                generated_files["html"] = str(permanent_html)

            # Generate PDF presentation
            pdf_file = generate_marp_pdf(marp_file, temp_path)
            if pdf_file and pdf_file.exists():
                permanent_pdf = save_generated_document(
                    pdf_file,
                        f"{business_data.get('id', 'unknown')}_{presentation_type}",
                        "pdf",
                        )
                generated_files["pdf"] = str(permanent_pdf)

            # Generate PowerPoint presentation
            pptx_file = generate_marp_pptx(marp_file, temp_path)
            if pptx_file and pptx_file.exists():
                permanent_pptx = save_generated_document(
                    pptx_file,
                        f"{business_data.get('id', 'unknown')}_{presentation_type}",
                        "pptx",
                        )
                generated_files["pptx"] = str(permanent_pptx)

            logger.info(f"Marketing presentation creation completed")
            return {
                "status": "success",
                    "business_id": business_data.get("id"),
                    "business_name": business_data.get("name"),
                    "presentation_type": presentation_type,
                    "generated_files": generated_files,
                    "slide_count": count_presentation_slides(marp_content),
                    "generated_at": datetime.utcnow().isoformat(),
                    }

    except Exception as e:
        logger.error(f"Marketing presentation creation failed: {str(e)}")
        raise self.retry(exc = e)

@celery_app.task(base = DocumentProcessingTask, bind = True)


def generate_business_reports(
    self, analytics_data: Dict[str, Any], report_types: List[str] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive business reports from analytics data

    Args:
        analytics_data: Business analytics and performance data
        report_types: Types of reports to generate (financial,
    performance,
    marketing,
    customer)

    Returns:
        Dict containing generated report files
    """
    try:
        logger.info(
            f"Generating business reports for period {analytics_data.get('period', 'unknown')}"
        )

        if report_types is None:
            report_types = ["financial", "performance"]

        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            generated_reports = {}

            for report_type in report_types:
                try:
                    # Generate report content
                    report_content = generate_report_content(
                        analytics_data, report_type
                    )

                    # Create markdown file
                    report_file = temp_path / f"{report_type}_report.md"
                    with open(report_file, "w", encoding="utf - 8") as f:
                        f.write(report_content)

                    # Generate PDF report
                    pdf_file = generate_styled_pdf_report(
                        report_file, temp_path, report_type, analytics_data
                    )

                    if pdf_file and pdf_file.exists():
                        permanent_pdf = save_generated_document(
                            pdf_file,
                                f"business_report_{report_type}_{analytics_data.get('period', 'current')}",
                                "pdf",
                                )
                        generated_reports[report_type] = {
                            "pdf": str(permanent_pdf),
                                "pages": count_pdf_pages(pdf_file),
                                "size_mb": get_file_size_mb(pdf_file),
                                }

                except Exception as e:
                    logger.error(f"Failed to generate {report_type} report: {str(e)}")
                    generated_reports[report_type] = {"error": str(e)}

            logger.info(f"Business reports generation completed")
            return {
                "status": "success",
                    "period": analytics_data.get("period"),
                    "generated_reports": generated_reports,
                    "report_types_requested": report_types,
                    "report_types_generated": [
                    r
                    for r in generated_reports.keys()
                    if "error" not in generated_reports[r]
                ],
                    "generated_at": datetime.utcnow().isoformat(),
                    }

    except Exception as e:
        logger.error(f"Business reports generation failed: {str(e)}")
        raise self.retry(exc = e)

@celery_app.task(base = DocumentProcessingTask, bind = True)


def create_product_catalog(
    self, products_data: List[Dict[str, Any]], catalog_style: str = "modern"
) -> Dict[str, Any]:
    """
    Create comprehensive product catalog with multiple products

    Args:
        products_data: List of product information
        catalog_style: Visual style for catalog (modern, classic, minimal)

    Returns:
        Dict containing catalog files and metadata
    """
    try:
        logger.info(f"Creating product catalog with {len(products_data)} products")

        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Generate catalog content
            catalog_content = generate_catalog_content(products_data, catalog_style)

            # Write catalog markdown
            catalog_file = temp_path / "product_catalog.md"
            with open(catalog_file, "w", encoding="utf - 8") as f:
                f.write(catalog_content)

            # Generate catalog in multiple formats
            generated_files = {}

            # Generate PDF catalog
            pdf_file = generate_styled_catalog_pdf(
                catalog_file, temp_path, catalog_style, products_data
            )

            if pdf_file and pdf_file.exists():
                permanent_pdf = save_generated_document(
                    pdf_file,
                        f"product_catalog_{catalog_style}_{datetime.now().strftime('%Y % m%d')}",
                        "pdf",
                        )
                generated_files["pdf"] = {
                    "path": str(permanent_pdf),
                        "pages": count_pdf_pages(pdf_file),
                        "size_mb": get_file_size_mb(pdf_file),
                        }

            # Generate HTML catalog
            html_file = generate_interactive_catalog_html(
                catalog_file, temp_path, catalog_style, products_data
            )

            if html_file and html_file.exists():
                permanent_html = save_generated_document(
                    html_file,
                        f"product_catalog_{catalog_style}_{datetime.now().strftime('%Y % m%d')}",
                        "html",
                        )
                generated_files["html"] = {
                    "path": str(permanent_html),
                        "size_mb": get_file_size_mb(html_file),
                        }

            # Generate EPUB catalog for e - readers
            epub_file = generate_catalog_epub(catalog_file, temp_path, products_data)

            if epub_file and epub_file.exists():
                permanent_epub = save_generated_document(
                    epub_file,
                        f"product_catalog_{catalog_style}_{datetime.now().strftime('%Y % m%d')}",
                        "epub",
                        )
                generated_files["epub"] = {
                    "path": str(permanent_epub),
                        "size_mb": get_file_size_mb(epub_file),
                        }

            logger.info(f"Product catalog creation completed")
            return {
                "status": "success",
                    "product_count": len(products_data),
                    "catalog_style": catalog_style,
                    "generated_files": generated_files,
                    "formats_generated": list(generated_files.keys()),
                    "generated_at": datetime.utcnow().isoformat(),
                    }

    except Exception as e:
        logger.error(f"Product catalog creation failed: {str(e)}")
        raise self.retry(exc = e)

@celery_app.task(base = DocumentProcessingTask, bind = True)


def generate_legal_documents(
    self, business_data: Dict[str, Any], document_types: List[str] = None
) -> Dict[str, Any]:
    """
    Generate legal documents for business operations

    Args:
        business_data: Business information and legal requirements
        document_types: Types of legal documents (terms, privacy, refund, license)

    Returns:
        Dict containing generated legal document files
    """
    try:
        logger.info(
            f"Generating legal documents for {business_data.get('name', 'Unknown Business')}"
        )

        if document_types is None:
            document_types = ["terms", "privacy"]

        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            generated_documents = {}

            for doc_type in document_types:
                try:
                    # Generate legal document content
                    legal_content = generate_legal_document_content(
                        business_data, doc_type
                    )

                    # Create markdown file
                    legal_file = temp_path / f"{doc_type}_document.md"
                    with open(legal_file, "w", encoding="utf - 8") as f:
                        f.write(legal_content)

                    # Generate PDF document
                    pdf_file = generate_legal_pdf(
                        legal_file, temp_path, doc_type, business_data
                    )

                    if pdf_file and pdf_file.exists():
                        permanent_pdf = save_generated_document(
                            pdf_file,
                                f"{business_data.get('id', 'unknown')}_{doc_type}_legal",
                                "pdf",
                                )

                        # Also generate HTML version for web display
                        html_file = generate_legal_html(
                            legal_file, temp_path, doc_type, business_data
                        )

                        permanent_html = None
                        if html_file and html_file.exists():
                            permanent_html = save_generated_document(
                                html_file,
                                    f"{business_data.get('id', 'unknown')}_{doc_type}_legal",
                                    "html",
                                    )

                        generated_documents[doc_type] = {
                            "pdf": str(permanent_pdf),
                                "html": str(permanent_html) if permanent_html else None,
                                "pages": count_pdf_pages(pdf_file),
                                "word_count": count_document_words(legal_content),
                                "last_updated": datetime.utcnow().isoformat(),
                                }

                except Exception as e:
                    logger.error(
                        f"Failed to generate {doc_type} legal document: {str(e)}"
                    )
                    generated_documents[doc_type] = {"error": str(e)}

            logger.info(f"Legal documents generation completed")
            return {
                "status": "success",
                    "business_id": business_data.get("id"),
                    "business_name": business_data.get("name"),
                    "generated_documents": generated_documents,
                    "document_types_requested": document_types,
                    "document_types_generated": [
                    d
                    for d in generated_documents.keys()
                    if "error" not in generated_documents[d]
                ],
                    "generated_at": datetime.utcnow().isoformat(),
                    }

    except Exception as e:
        logger.error(f"Legal documents generation failed: {str(e)}")
        raise self.retry(exc = e)

@celery_app.task(base = DocumentProcessingTask, bind = True)


def create_training_materials(
    self, course_data: Dict[str, Any], material_types: List[str] = None
) -> Dict[str, Any]:
    """
    Create comprehensive training materials and courses

    Args:
        course_data: Course content and structure information
        material_types: Types of materials (slides, workbook, video_script, quiz)

    Returns:
        Dict containing generated training material files
    """
    try:
        logger.info(
            f"Creating training materials for {course_data.get('title', 'Unknown Course')}"
        )

        if material_types is None:
            material_types = ["slides", "workbook"]

        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            generated_materials = {}

            for material_type in material_types:
                try:
                    if material_type == "slides":
                        # Generate presentation slides
                        slides_result = create_training_slides(course_data, temp_path)
                        generated_materials["slides"] = slides_result

                    elif material_type == "workbook":
                        # Generate student workbook
                        workbook_result = create_training_workbook(
                            course_data, temp_path
                        )
                        generated_materials["workbook"] = workbook_result

                    elif material_type == "video_script":
                        # Generate video scripts
                        script_result = create_video_scripts(course_data, temp_path)
                        generated_materials["video_script"] = script_result

                    elif material_type == "quiz":
                        # Generate assessment quizzes
                        quiz_result = create_assessment_quizzes(course_data, temp_path)
                        generated_materials["quiz"] = quiz_result

                except Exception as e:
                    logger.error(
                        f"Failed to generate {material_type} training material: {str(e)}"
                    )
                    generated_materials[material_type] = {"error": str(e)}

            logger.info(f"Training materials creation completed")
            return {
                "status": "success",
                    "course_id": course_data.get("id"),
                    "course_title": course_data.get("title"),
                    "generated_materials": generated_materials,
                    "material_types_requested": material_types,
                    "material_types_generated": [
                    m
                    for m in generated_materials.keys()
                    if "error" not in generated_materials[m]
                ],
                    "generated_at": datetime.utcnow().isoformat(),
                    }

    except Exception as e:
        logger.error(f"Training materials creation failed: {str(e)}")
        raise self.retry(exc = e)

# Content generation functions


def generate_product_markdown(product_data: Dict[str, Any]) -> str:
    """Generate comprehensive product documentation in markdown format"""

    template = Template(
        """
# {{ product.name }}

## Product Overview

{{ product.description }}

## Key Features

{% for feature in product.features %}
- **{{ feature.name }}**: {{ feature.description }}
{% endfor %}

## Technical Specifications

{% if product.specifications %}
| Specification | Value |
|---------------|-------|
{% for spec_name, spec_value in product.specifications.items() %}
| {{ spec_name }} | {{ spec_value }} |
{% endfor %}
{% endif %}

## Pricing

**Price**: ${{ product.price }}
{% if product.discount_price %}
**Discounted Price**: ${{ product.discount_price }}
{% endif %}

## Usage Instructions

{{ product.usage_instructions | default('Detailed usage instructions will be provided upon purchase.') }}

## Support

For technical support,
    please contact: {{ product.support_email | default('support@example.com') }}

## License

{{ product.license_info | default('Standard commercial license applies.') }}

---

*Generated on {{ generated_date }}*
    """
    )

    return template.render(
        product = product_data,
            generated_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            )


def generate_marp_presentation(
    business_data: Dict[str, Any], presentation_type: str
) -> str:
    """Generate Marp presentation content"""

    if presentation_type == "pitch":
        return generate_pitch_presentation(business_data)
    elif presentation_type == "product":
        return generate_product_presentation(business_data)
    elif presentation_type == "training":
        return generate_training_presentation(business_data)
    elif presentation_type == "report":
        return generate_report_presentation(business_data)
    else:
        return generate_generic_presentation(business_data)


def generate_pitch_presentation(business_data: Dict[str, Any]) -> str:
    """Generate business pitch presentation"""

    template = Template(
        """
---
marp: true
theme: default
class: lead
paginate: true
backgroundColor: #fff
---

# {{ business.name }}

## {{ business.tagline | default('Revolutionizing the Industry') }}

*{{ business.founder | default('Entrepreneur') }}*
*{{ generated_date }}*

---

# The Problem

## {{ business.problem.title | default('Market Challenge') }}

{{ business.problem.description | default('There is a significant gap in the market that needs to be addressed.') }}

### Key Pain Points:
{% for pain_point in business.problem.pain_points | default(['Market inefficiency', 'Customer dissatisfaction', 'High costs']) %}
- {{ pain_point }}
{% endfor %}

---

# Our Solution

## {{ business.solution.title | default('Innovative Approach') }}

{{ business.solution.description | default('We provide a comprehensive solution that addresses all market pain points.') }}

### Key Benefits:
{% for benefit in business.solution.benefits | default(['Increased efficiency', 'Better user experience', 'Cost reduction']) %}
- {{ benefit }}
{% endfor %}

---

# Market Opportunity

## Target Market Size

- **Total Addressable Market (TAM)**: ${{ business.market.tam | default('10B') }}
- **Serviceable Addressable Market (SAM)**: ${{ business.market.sam | default('1B') }}
- **Serviceable Obtainable Market (SOM)**: ${{ business.market.som | default('100M') }}

### Growth Projections:
- Year 1: ${{ business.projections.year1 | default('1M') }}
- Year 3: ${{ business.projections.year3 | default('10M') }}
- Year 5: ${{ business.projections.year5 | default('50M') }}

---

# Business Model

## Revenue Streams

{% for stream in business.revenue_streams | default([{'name': 'Primary Product Sales', 'description': 'Direct sales of our main product'}]) %}
### {{ stream.name }}
{{ stream.description }}
{% endfor %}

---

# Competitive Advantage

{% for advantage in business.competitive_advantages | default(['Unique technology', 'Strong team', 'Market timing']) %}
## {{ advantage }}
{% endfor %}

---

# Financial Projections

| Year | Revenue | Expenses | Profit |
|------|---------|----------|--------|
{% for year in business.financial_projections | default([{'year': 1, 'revenue': '1M', 'expenses': '800K', 'profit': '200K'}]) %}
| {{ year.year }} | ${{ year.revenue }} | ${{ year.expenses }} | ${{ year.profit }} |
{% endfor %}

---

# Team

{% for member in business.team | default([{'name': 'Founder', 'role': 'CEO', 'background': 'Industry expert'}]) %}
## {{ member.name }}
**{{ member.role }}**
{{ member.background }}
{% endfor %}

---

# Funding Request

## We are seeking ${{ business.funding.amount | default('1M') }}

### Use of Funds:
{% for use in business.funding.use_of_funds | default([{'category': 'Product Development', 'percentage': 40}, {'category': 'Marketing', 'percentage': 30}, {'category': 'Operations', 'percentage': 30}]) %}
- **{{ use.category }}**: {{ use.percentage }}%
{% endfor %}

---

# Thank You

## Questions?

**Contact Information:**
- Email: {{ business.contact.email | default('contact@business.com') }}
- Phone: {{ business.contact.phone | default('+1 (555) 123 - 4567') }}
- Website: {{ business.contact.website | default('www.business.com') }}

*Let's build the future together!*
    """
    )

    return template.render(
        business = business_data,
    generated_date = datetime.utcnow().strftime("%B %d, %Y")
    )


def generate_report_content(analytics_data: Dict[str, Any], report_type: str) -> str:
    """Generate business report content"""

    if report_type == "financial":
        return generate_financial_report(analytics_data)
    elif report_type == "performance":
        return generate_performance_report(analytics_data)
    elif report_type == "marketing":
        return generate_marketing_report(analytics_data)
    elif report_type == "customer":
        return generate_customer_report(analytics_data)
    else:
        return generate_generic_report(analytics_data)


def generate_financial_report(analytics_data: Dict[str, Any]) -> str:
    """Generate financial performance report"""

    template = Template(
        """
# Financial Performance Report

**Reporting Period**: {{ period }}
**Generated**: {{ generated_date }}

## Executive Summary

This report provides a comprehensive overview of financial performance for the period {{ period }}.

### Key Metrics
- **Total Revenue**: ${{ metrics.total_revenue | default(0) | round(2) }}
- **Total Expenses**: ${{ metrics.total_expenses | default(0) | round(2) }}
- **Net Profit**: ${{ metrics.net_profit | default(0) | round(2) }}
- **Profit Margin**: {{ metrics.profit_margin | default(0) | round(1) }}%

## Revenue Analysis

### Revenue by Source
{% for source, amount in revenue_sources.items() %}
- **{{ source }}**: ${{ amount | round(2) }} ({{ (amount / metrics.total_revenue * 100) | round(1) }}%)
{% endfor %}

### Revenue Trends
{{ revenue_trend_analysis | default('Revenue has shown steady growth throughout the reporting period.') }}

## Expense Analysis

### Expense Categories
{% for category, amount in expense_categories.items() %}
- **{{ category }}**: ${{ amount | round(2) }} ({{ (amount / metrics.total_expenses * 100) | round(1) }}%)
{% endfor %}

## Profitability Analysis

### Gross Profit Margin
{{ profitability.gross_margin | default(0) | round(1) }}%

### Operating Profit Margin
{{ profitability.operating_margin | default(0) | round(1) }}%

### Net Profit Margin
{{ profitability.net_margin | default(0) | round(1) }}%

## Cash Flow Analysis

- **Operating Cash Flow**: ${{ cash_flow.operating | default(0) | round(2) }}
- **Investing Cash Flow**: ${{ cash_flow.investing | default(0) | round(2) }}
- **Financing Cash Flow**: ${{ cash_flow.financing | default(0) | round(2) }}
- **Net Cash Flow**: ${{ cash_flow.net | default(0) | round(2) }}

## Key Performance Indicators

| KPI | Current Period | Previous Period | Change |
|-----|----------------|-----------------|--------|
{% for kpi in kpis %}
| {{ kpi.name }} | {{ kpi.current }} | {{ kpi.previous }} | {{ kpi.change }} |
{% endfor %}

## Recommendations

{% for recommendation in recommendations %}
### {{ recommendation.title }}
{{ recommendation.description }}

**Expected Impact**: {{ recommendation.impact }}
**Timeline**: {{ recommendation.timeline }}
{% endfor %}

## Conclusion

{{ conclusion | default('The financial performance for this period shows positive trends with opportunities for continued growth.') }}

---

*This report was automatically generated on {{ generated_date }}*
    """
    )

    return template.render(
        period = analytics_data.get("period", "Current Period"),
            metrics = analytics_data.get("metrics", {}),
            revenue_sources = analytics_data.get("revenue_sources", {}),
            expense_categories = analytics_data.get("expense_categories", {}),
            profitability = analytics_data.get("profitability", {}),
            cash_flow = analytics_data.get("cash_flow", {}),
            kpis = analytics_data.get("kpis", []),
            recommendations = analytics_data.get("recommendations", []),
            revenue_trend_analysis = analytics_data.get("revenue_trend_analysis"),
            conclusion = analytics_data.get("conclusion"),
            generated_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            )


def generate_catalog_content(
    products_data: List[Dict[str, Any]], catalog_style: str
) -> str:
    """Generate product catalog content"""

    template = Template(
        """
# Product Catalog

**{{ catalog_title | default('Our Product Collection') }}**

*{{ catalog_description | default('Discover our comprehensive range of high - quality products designed to meet your needs.') }}*

---

{% for product in products %}
## {{ product.name }}

{% if product.image_url %}
![{{ product.name }}]({{ product.image_url }})
{% endif %}

### Description
{{ product.description }}

### Key Features
{% for feature in product.features | default([]) %}
- {{ feature }}
{% endfor %}

### Specifications
{% if product.specifications %}
{% for spec_name, spec_value in product.specifications.items() %}
- **{{ spec_name }}**: {{ spec_value }}
{% endfor %}
{% endif %}

### Pricing
**Price**: ${{ product.price }}
{% if product.discount_price %}
~~${{ product.price }}~~ **${{ product.discount_price }}** *({{ ((product.price - product.discount_price)/product.price * 100) | round(0) }}% off)*
{% endif %}

{% if product.availability %}
**Availability**: {{ product.availability }}
{% endif %}

---

{% endfor %}

## Contact Information

For more information about any of our products, please contact us:

- **Email**: {{ contact.email | default('info@company.com') }}
- **Phone**: {{ contact.phone | default('+1 (555) 123 - 4567') }}
- **Website**: {{ contact.website | default('www.company.com') }}

## Terms and Conditions

{{ terms | default('All prices are subject to change without notice. Please contact us for the most current pricing \
    and availability.') }}

---

*Catalog generated on {{ generated_date }}*
    """
    )

    return template.render(
        products = products_data,
            catalog_title = f"Product Catalog - {catalog_style.title()} Style",
            catalog_description="Explore our curated collection of premium products.",
            contact={
            "email": "sales@company.com",
                "phone": "+1 (555) 123 - 4567",
                "website": "www.company.com",
                },
            terms="All products come with our standard warranty. Prices \
    and availability subject to change.",
            generated_date = datetime.utcnow().strftime("%B %d, %Y"),
            )


def generate_legal_document_content(
    business_data: Dict[str, Any], doc_type: str
) -> str:
    """Generate legal document content"""

    if doc_type == "terms":
        return generate_terms_of_service(business_data)
    elif doc_type == "privacy":
        return generate_privacy_policy(business_data)
    elif doc_type == "refund":
        return generate_refund_policy(business_data)
    elif doc_type == "license":
        return generate_license_agreement(business_data)
    else:
        return generate_generic_legal_document(business_data, doc_type)


def generate_terms_of_service(business_data: Dict[str, Any]) -> str:
    """Generate Terms of Service document"""

    template = Template(
        """
# Terms of Service

**{{ business.name }}**

*Last Updated: {{ last_updated }}*

## 1. Acceptance of Terms

By accessing \
    and using {{ business.name }}'s services, you accept \
    and agree to be bound by the terms \
    and provision of this agreement.

## 2. Description of Service

{{ business.name }} provides {{ business.service_description | default('digital products \
    and services') }} to customers worldwide.

## 3. User Responsibilities

Users are responsible for:
- Providing accurate information
- Maintaining the confidentiality of account credentials
- Using services in compliance with applicable laws
- Respecting intellectual property rights

## 4. Payment Terms

- All payments are processed securely through our payment partners
- Prices are displayed in USD unless otherwise specified
- Payment is required before access to digital products
- We reserve the right to change prices at any time

## 5. Intellectual Property

All content, trademarks, \
    and intellectual property on this platform are owned by {{ business.name }} or our licensors.

## 6. Limitation of Liability

{{ business.name }} shall not be liable for any indirect, incidental, special, consequential, \
    or punitive damages.

## 7. Termination

We reserve the right to terminate \
    or suspend access to our services at any time, without prior notice.

## 8. Governing Law

These terms shall be governed by the laws of {{ business.jurisdiction | default('the United States') }}.

## 9. Contact Information

For questions about these Terms of Service, please contact us at:
- Email: {{ business.legal_email | default('legal@company.com') }}
- Address: {{ business.address | default('123 Business St, City, State 12345') }}

## 10. Changes to Terms

We reserve the right to modify these terms at any time. Changes will be effective immediately upon posting.

---

*This document was generated on {{ generated_date }}*
    """
    )

    return template.render(
        business = business_data,
            last_updated = datetime.utcnow().strftime("%B %d, %Y"),
            generated_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            )

# Document generation helper functions


def generate_document_format(
    markdown_file: Path,
        format_type: str,
        temp_path: Path,
        metadata: Dict[str, Any] = None,
) -> Optional[Path]:
    """Generate document in specified format using Pandoc"""

    output_file = temp_path / f"document.{format_type}"

    try:
        # Build Pandoc command
            cmd = ["pandoc", str(markdown_file), "-o", str(output_file), "--standalone"]

        # Add format - specific options
        if format_type == "pdf":
            cmd.extend(
                [
                    "--pdf - engine = xelatex",
                        "--variable",
                        "geometry:margin = 1in",
                        "--variable",
                        "fontsize = 11pt",
                        ]
            )
        elif format_type == "html":
            cmd.extend(["--css", get_html_css_path(), "--self - contained"])
        elif format_type == "docx":
            cmd.extend(["--reference - doc", get_docx_template_path()])
        elif format_type == "epub":
            cmd.extend(["--epub - cover - image", get_default_cover_image()])

        # Add metadata if provided
        if metadata:
            for key, value in metadata.items():
                cmd.extend(["--variable", f"{key}:{value}"])

        # Execute Pandoc command
            result = subprocess.run(cmd,
    capture_output = True,
    text = True,
    check = True)

        if output_file.exists():
            return output_file
        else:
            logger.error(f"Pandoc did not generate output file: {output_file}")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"Pandoc failed to generate {format_type}: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error("Pandoc not found. Please install Pandoc to generate documents.")
        return None


def generate_marp_html(marp_file: Path, temp_path: Path) -> Optional[Path]:
    """Generate HTML presentation using Marp"""

    output_file = temp_path / "presentation.html"

    try:
        cmd = ["marp", str(marp_file), "--html", "--output", str(output_file)]

        result = subprocess.run(cmd, capture_output = True, text = True, check = True)

        if output_file.exists():
            return output_file
        else:
            logger.error(f"Marp did not generate HTML file: {output_file}")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"Marp failed to generate HTML: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error(
            "Marp not found. Please install Marp CLI to generate presentations."
        )
        return None


def generate_marp_pdf(marp_file: Path, temp_path: Path) -> Optional[Path]:
    """Generate PDF presentation using Marp"""

    output_file = temp_path / "presentation.pdf"

    try:
        cmd = ["marp", str(marp_file), "--pdf", "--output", str(output_file)]

        result = subprocess.run(cmd, capture_output = True, text = True, check = True)

        if output_file.exists():
            return output_file
        else:
            logger.error(f"Marp did not generate PDF file: {output_file}")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"Marp failed to generate PDF: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error(
            "Marp not found. Please install Marp CLI to generate presentations."
        )
        return None


def generate_marp_pptx(marp_file: Path, temp_path: Path) -> Optional[Path]:
    """Generate PowerPoint presentation using Marp"""

    output_file = temp_path / "presentation.pptx"

    try:
        cmd = ["marp", str(marp_file), "--pptx", "--output", str(output_file)]

        result = subprocess.run(cmd, capture_output = True, text = True, check = True)

        if output_file.exists():
            return output_file
        else:
            logger.error(f"Marp did not generate PPTX file: {output_file}")
            return None

    except subprocess.CalledProcessError as e:
        logger.error(f"Marp failed to generate PPTX: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error(
            "Marp not found. Please install Marp CLI to generate presentations."
        )
        return None


def save_generated_document(
    temp_file: Path, document_id: str, format_type: str
) -> Path:
    """Save generated document to permanent location"""

    # Create documents directory if it doesn't exist
    docs_dir = Path("generated_documents")
    docs_dir.mkdir(exist_ok = True)

    # Create subdirectory for document type
    type_dir = docs_dir / format_type
    type_dir.mkdir(exist_ok = True)

    # Generate permanent filename
    timestamp = datetime.utcnow().strftime("%Y % m%d_ % H%M % S")
    permanent_file = type_dir / f"{document_id}_{timestamp}.{format_type}"

    # Copy file to permanent location
    shutil.copy2(temp_file, permanent_file)

    return permanent_file

# Utility functions


def count_presentation_slides(marp_content: str) -> int:
    """Count number of slides in Marp presentation"""
    return marp_content.count("---") + 1


def count_pdf_pages(pdf_file: Path) -> int:
    """Count pages in PDF file"""
    try:
        # This would require PyPDF2 or similar library
        # For now, return estimated count
        file_size = pdf_file.stat().st_size
        estimated_pages = max(1, file_size // 50000)  # Rough estimate
        return estimated_pages
    except Exception:
        return 1


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes"""
    try:
        size_bytes = file_path.stat().st_size
        return round(size_bytes / (1024 * 1024), 2)
    except Exception:
        return 0.0


def count_document_words(content: str) -> int:
    """Count words in document content"""
    return len(content.split())

# Template and resource helper functions


def get_html_css_path() -> str:
    """Get path to HTML CSS template"""
    return "templates / document.css"


def get_docx_template_path() -> str:
    """Get path to DOCX template"""
    return "templates / document_template.docx"


def get_default_cover_image() -> str:
    """Get path to default cover image"""
    return "templates / default_cover.png"

# Stub functions for training materials (to be implemented)


def create_training_slides(
    course_data: Dict[str, Any], temp_path: Path
) -> Dict[str, Any]:
    """Create training presentation slides"""
    return {"status": "created", "slides": 25, "format": "html"}


def create_training_workbook(
    course_data: Dict[str, Any], temp_path: Path
) -> Dict[str, Any]:
    """Create student workbook"""
    return {"status": "created", "pages": 50, "format": "pdf"}


def create_video_scripts(
    course_data: Dict[str, Any], temp_path: Path
) -> Dict[str, Any]:
    """Create video scripts"""
    return {"status": "created", "scripts": 10, "total_duration": "2 hours"}


def create_assessment_quizzes(
    course_data: Dict[str, Any], temp_path: Path
) -> Dict[str, Any]:
    """Create assessment quizzes"""
    return {"status": "created", "quizzes": 5, "total_questions": 50}

# Additional stub functions for specialized document generation


def generate_styled_pdf_report(
    report_file: Path, temp_path: Path, report_type: str, analytics_data: Dict[str, Any]
) -> Optional[Path]:
    """Generate styled PDF report"""
    return generate_document_format(
        report_file, "pdf", temp_path, {"title": f"{report_type.title()} Report"}
    )


def generate_styled_catalog_pdf(
    catalog_file: Path,
        temp_path: Path,
        catalog_style: str,
        products_data: List[Dict[str, Any]],
) -> Optional[Path]:
    """Generate styled product catalog PDF"""
    return generate_document_format(
        catalog_file,
            "pdf",
            temp_path,
            {"title": f"Product Catalog - {catalog_style.title()}"},
            )


def generate_interactive_catalog_html(
    catalog_file: Path,
        temp_path: Path,
        catalog_style: str,
        products_data: List[Dict[str, Any]],
) -> Optional[Path]:
    """Generate interactive HTML catalog"""
    return generate_document_format(
        catalog_file, "html", temp_path, {"title": f"Interactive Product Catalog"}
    )


def generate_catalog_epub(
    catalog_file: Path, temp_path: Path, products_data: List[Dict[str, Any]]
) -> Optional[Path]:
    """Generate EPUB catalog for e - readers"""
    return generate_document_format(
        catalog_file, "epub", temp_path, {"title": "Product Catalog"}
    )


def generate_legal_pdf(
    legal_file: Path, temp_path: Path, doc_type: str, business_data: Dict[str, Any]
) -> Optional[Path]:
    """Generate legal document PDF"""
    return generate_document_format(
        legal_file,
            "pdf",
            temp_path,
            {"title": f'{doc_type.title()} - {business_data.get("name", "Business")}'},
            )


def generate_legal_html(
    legal_file: Path, temp_path: Path, doc_type: str, business_data: Dict[str, Any]
) -> Optional[Path]:
    """Generate legal document HTML"""
    return generate_document_format(
        legal_file,
            "html",
            temp_path,
            {"title": f'{doc_type.title()} - {business_data.get("name", "Business")}'},
            )

# Additional content generation stubs


def generate_product_presentation(business_data: Dict[str, Any]) -> str:
    """Generate product - focused presentation"""
    return generate_pitch_presentation(business_data)  # Use pitch template for now


def generate_training_presentation(business_data: Dict[str, Any]) -> str:
    """Generate training presentation"""
    return generate_pitch_presentation(business_data)  # Use pitch template for now


def generate_report_presentation(business_data: Dict[str, Any]) -> str:
    """Generate report presentation"""
    return generate_pitch_presentation(business_data)  # Use pitch template for now


def generate_generic_presentation(business_data: Dict[str, Any]) -> str:
    """Generate generic presentation"""
    return generate_pitch_presentation(business_data)  # Use pitch template for now


def generate_performance_report(analytics_data: Dict[str, Any]) -> str:
    """Generate performance report"""
    return generate_financial_report(analytics_data)  # Use financial template for now


def generate_marketing_report(analytics_data: Dict[str, Any]) -> str:
    """Generate marketing report"""
    return generate_financial_report(analytics_data)  # Use financial template for now


def generate_customer_report(analytics_data: Dict[str, Any]) -> str:
    """Generate customer report"""
    return generate_financial_report(analytics_data)  # Use financial template for now


def generate_generic_report(analytics_data: Dict[str, Any]) -> str:
    """Generate generic report"""
    return generate_financial_report(analytics_data)  # Use financial template for now


def generate_privacy_policy(business_data: Dict[str, Any]) -> str:
    """Generate Privacy Policy document"""
    return generate_terms_of_service(business_data)  # Use terms template for now


def generate_refund_policy(business_data: Dict[str, Any]) -> str:
    """Generate Refund Policy document"""
    return generate_terms_of_service(business_data)  # Use terms template for now


def generate_license_agreement(business_data: Dict[str, Any]) -> str:
    """Generate License Agreement document"""
    return generate_terms_of_service(business_data)  # Use terms template for now


def generate_generic_legal_document(
    business_data: Dict[str, Any], doc_type: str
) -> str:
    """Generate generic legal document"""
    return generate_terms_of_service(business_data)  # Use terms template for now