"""Recruitment UI copy; the job's own content remains HR-owned."""

EN = {
    "requirements": "Qualifications & skills", "degree": "Education",
    "skills": "Required skills", "level": "Expected level", "role_facts": "Role at a glance",
    "requirements_note": "These are the qualifications and skill levels expected for this role.",
    "vacancy": "Job vacancy", "review_role": "Explore the role", "apply_note": "Tell us how your experience matches this opportunity.",
    "share_facebook": "Share on Facebook",
    "copy_link": "Copy job link", "copied": "Link copied", "copy_failed": "Select and copy the link below.",
    "eyebrow": "Careers", "title": "Build the future of payments in Yemen",
    "lead": "Explore published opportunities at MASAR Pay and apply for a role that matches your experience.",
    "opportunities": "Open opportunities", "search": "Search jobs", "search_placeholder": "Job title or keyword",
    "empty_title": "No open opportunities right now", "empty": "New opportunities will appear here when they are published. Please check back later.",
    "no_results": "No jobs match your search", "reset": "View all opportunities",
    "apply": "Apply for this role", "details": "View role", "back": "All opportunities",
    "location": "Location", "remote": "Location not specified", "department": "Department",
    "type": "Employment type", "description": "About this role", "description_pending": "For more information about this opportunity, contact the MASAR team.",
    "process_title": "How to apply", "process": "Review the role, then submit your professional information and your CV or LinkedIn profile through the application form.",
    "contact": "Contact us", "draft": "Unpublished preview — this role is not visible to visitors",
    "form_title": "Apply to MASAR Pay", "submit": "Submit application",
    "form_note": "Provide accurate professional information and a CV or LinkedIn profile. Do not include identity documents or financial information.",
    "process_note": "The recruitment team will review your application and contact you if your profile matches the role.",
    "received": "Your application has been received", "thanks": "Thank you for your interest in MASAR Pay. The recruitment team will review your application.",
}

AR = {
    "requirements": "المؤهلات والمهارات", "degree": "المؤهل العلمي",
    "skills": "المهارات المطلوبة", "level": "المستوى المطلوب", "role_facts": "الوظيفة باختصار",
    "requirements_note": "هذه المؤهلات ومستويات المهارات المطلوبة لهذه الوظيفة.",
    "vacancy": "وظيفة شاغرة", "review_role": "تعرّف على الوظيفة", "apply_note": "وضّح كيف تتناسب خبرتك مع هذه الفرصة.",
    "share_facebook": "مشاركة على فيسبوك",
    "copy_link": "نسخ رابط الوظيفة", "copied": "تم نسخ الرابط", "copy_failed": "حدّد الرابط أدناه وانسخه.",
    "eyebrow": "الوظائف", "title": "ساهم في تطوير مستقبل المدفوعات في اليمن",
    "lead": "تعرّف على الفرص المنشورة لدى مسار Pay، وقدّم للوظيفة التي تناسب خبرتك.",
    "opportunities": "الفرص المتاحة", "search": "ابحث عن وظيفة", "search_placeholder": "المسمى الوظيفي أو كلمة مفتاحية",
    "empty_title": "لا توجد فرص متاحة حاليًا", "empty": "ستظهر الفرص الجديدة هنا عند نشرها. يمكنك زيارة الصفحة لاحقًا للاطلاع على المستجدات.",
    "no_results": "لا توجد وظائف تطابق بحثك", "reset": "عرض جميع الفرص",
    "apply": "قدّم لهذه الوظيفة", "details": "تفاصيل الوظيفة", "back": "جميع الفرص",
    "location": "الموقع", "remote": "الموقع غير محدد", "department": "القسم",
    "type": "نوع التوظيف", "description": "عن الوظيفة", "description_pending": "لمزيد من المعلومات عن هذه الفرصة، تواصل مع فريق مسار.",
    "process_title": "طريقة التقديم", "process": "راجع تفاصيل الوظيفة، ثم أرسل معلوماتك المهنية وسيرتك الذاتية أو رابط حسابك على LinkedIn عبر نموذج التقديم.",
    "contact": "تواصل معنا", "draft": "معاينة غير منشورة — هذه الوظيفة لا تظهر لزوار الموقع",
    "form_title": "التقديم لدى مسار Pay", "submit": "إرسال طلب التوظيف",
    "form_note": "قدّم معلومات مهنية دقيقة وسيرتك الذاتية أو رابط حسابك على LinkedIn. لا تُرفق وثائق الهوية أو البيانات المالية.",
    "process_note": "يراجع فريق التوظيف طلبك ويتواصل معك إذا كانت خبرتك مناسبة للوظيفة.",
    "received": "تم استلام طلب التوظيف", "thanks": "شكرًا لاهتمامك بالانضمام إلى مسار Pay. سيراجع فريق التوظيف طلبك.",
}


def get_careers_copy(lang):
    return dict(AR if (lang or "").startswith("ar") else EN)
