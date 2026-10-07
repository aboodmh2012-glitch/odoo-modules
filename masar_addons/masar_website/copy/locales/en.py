"""Central public website content. Updated 28 September 2026."""

CATALOG = {'skip': 'Skip to content',
 'nav_label': 'Primary',
 'nav_toggle': 'Menu',
 'lang_label': 'Language',
 'brand': {'name': 'MASAR Pay',
           'mark': 'MASAR',
           'product': 'Pay',
           'tagline': 'ONE MASAR. EVERY PAYMENT.',
           'promotion': 'MASAR Payment Gateway',
           'rights': 'MASAR Pay. All rights reserved.',
           'meta_title': 'MASAR Pay — One Path for All Your Payments',
           'meta_description': 'Explore MASAR Pay’s payment solutions in Yemen: payment gateway, POS, '
                               'accounts and cards, bulk payments, bill payments, and cash services.'},
 'actions': {'get_started': 'Request a Service',
             'get_started_href': '/contactus',
             'explore_services': 'Explore Our Services',
             'explore_services_href': '/solutions',
             'contact': 'Contact Us',
             'contact_href': '/contactus',
             'explore_business': 'Explore Business Solutions',
             'explore_business_href': '/business',
             'explore_personal': 'Explore Personal Services',
             'explore_personal_href': '/individuals',
             'learn_about': 'Learn More About MASAR',
             'learn_about_href': '/about',
             'subscribe': 'Subscribe',
             'email_placeholder': 'Enter your email',
             'email_label': 'Email address',
             'carousel_prev': 'Previous service',
             'carousel_next': 'Next service'},
 'nav': [{'id': 'home', 'label': 'Home', 'href': '/'},
         {'id': 'about', 'label': 'About Us', 'href': '/about'},
         {'id': 'services', 'label': 'Services', 'href': '/solutions'},
         {'id': 'business', 'label': 'Businesses', 'href': '/business'},
         {'id': 'individuals', 'label': 'Individuals', 'href': '/individuals'},
         {'id': 'developers', 'label': 'Developers', 'href': '/developers'},
         {'id': 'support', 'label': 'Support', 'href': '/support'}],
 'home': {'seo_title': 'MASAR Pay — One Path for All Your Payments',
          'seo_description': 'Explore MASAR Pay’s payment solutions in Yemen: payment gateway, POS, accounts '
                             'and cards, bulk payments, bill payments, and cash services.',
          'hero': {'eyebrow': 'Yemen’s First Electronic Payment Gateway',
                   'title_parts': [{'text': 'One', 'tone': 'default', 'break_before': False},
                                   {'text': 'Path', 'tone': 'accent', 'break_before': False},
                                   {'text': 'for All Your Payments',
                                    'tone': 'default',
                                    'break_before': True}],
                   'lead': 'Connecting people and businesses with solutions that simplify accepting and '
                           'managing payments online and in person, supporting Yemen’s digital economy.',
                   'metrics': [{'value': '1,248', 'label': 'Transactions'},
                               {'value': '342,250', 'label': 'Volume'},
                               {'value': '96%', 'label': 'Success'},
                               {'value': '98%', 'label': 'Activity'}],
                   'phone_apps': ['Pay', 'Transfer', 'Bills', 'Cards', 'Top up', 'More']},
          'services_intro': {'eyebrow': 'Our Services',
                             'title': 'Connected Solutions for Your Payment Needs',
                             'lead': 'From customer payments to payroll and bills, explore MASAR’s services '
                                     'and find the right solution for you.'},
          'trust': [{'icon': 'shield', 'title': 'Payment Acceptance', 'text': 'Online and in person'},
                    {'icon': 'bolt', 'title': 'Business Integration', 'text': 'Options for your business'},
                    {'icon': 'chart',
                     'title': 'Transaction Visibility',
                     'text': 'Payment status and records'},
                    {'icon': 'headset',
                     'title': 'Local Understanding',
                     'text': 'Built around Yemen’s needs'}],
          'offers': [{'icon': 'gateway',
                      'title': 'Payment Gateway',
                      'text': 'Connect your website and app with supported payment methods and track '
                              'payments linked to customer orders.',
                      'href': '/solutions#gateway'},
                     {'icon': 'pos',
                      'title': 'POS Solutions',
                      'text': 'Explore payment acceptance in store and at the point of service.',
                      'href': '/solutions#pos'},
                     {'icon': 'card',
                      'title': 'Accounts & Cards',
                      'text': 'Solutions for managing balances, payments, and spending.',
                      'href': '/solutions#accounts'},
                     {'icon': 'bulk',
                      'title': 'Bulk Payments',
                      'text': 'Organise payroll and other payouts to multiple recipients and track results.',
                      'href': '/solutions#bulk'},
                     {'icon': 'bill',
                      'title': 'Bill Payments',
                      'text': 'Pay connected providers and keep track of your bill payments.',
                      'href': '/solutions#bills'},
                     {'icon': 'atm',
                      'title': 'ATMs & Cash',
                      'text': 'Explore available withdrawal, deposit, and service locations.',
                      'href': '/solutions#atm'}],
          'audiences': [{'tone': 'business',
                         'kicker': 'For Businesses',
                         'title': 'Payment Solutions for Growing Businesses',
                         'points': ['Accept payments through your business channels',
                                    'Track transactions and settlements',
                                    'Reports for review and reconciliation',
                                    'Explore integration options for your systems'],
                         'action': 'explore_business'},
                        {'tone': 'personal',
                         'kicker': 'For Individuals',
                         'title': 'Simpler Everyday Payments',
                         'points': ['Accounts and cards to organise payments',
                                    'Money transfers and bill payments',
                                    'Balance and transaction tracking',
                                    'Clear requirements, fees, and limits'],
                         'action': 'explore_personal'}],
          'principles': [{'icon': 'values',
                          'title': 'Our Values',
                          'lines': ['Trust', 'Integration', 'Innovation', 'Social Responsibility']},
                         {'icon': 'mission',
                          'title': 'Our Mission',
                          'text': 'To build secure, scalable payment and acceptance solutions that connect '
                                  'people and businesses with Yemen’s payment ecosystem and simplify how '
                                  'transactions are made and managed.'},
                         {'icon': 'vision',
                          'title': 'Our Vision',
                          'text': 'To make payments in Yemen more connected, accessible, and effortless.'},
                         {'icon': 'goals',
                          'title': 'Our Goals',
                          'text': 'Widen access to trusted digital payments, connect more people and '
                                  'businesses to Yemen’s financial system, and make every transaction clearer '
                                  'to complete.'}],
          'path_banner': {'icon': 'path',
                          'title': 'MASAR Pay — One Path',
                          'text': 'MASAR Pay is a Yemeni company specialising in payment technologies and '
                                  'services, operating as a payment service provider and payment system '
                                  'operator. We connect people and businesses with payment channels through '
                                  'integration with banks, digital wallets, and financial and technology '
                                  'institutions.',
                          'link': 'learn_about'},
          'opportunity': {'title': 'From Yemen\nto Greater Opportunities'},
          'closing': {'title': 'Find the Right Payment Solution for You',
                      'lead': 'Tell us what you need. Our team will help you explore available options and '
                              'understand the requirements.'}},
 'footer': {'newsletter_title': 'Stay Updated with MASAR',
            'newsletter_ok': 'Thank you. Your email is registered.',
            'newsletter_invalid': 'Enter a valid email address.',
            'partners_caption': 'Broader partners\nfor a better future',
            'social': [{'id': 'facebook', 'icon': 'fa fa-facebook', 'label': 'Facebook', 'href': 'https://www.facebook.com/MsarPay/'},
                       {'id': 'instagram', 'icon': 'fa fa-instagram', 'label': 'Instagram', 'href': 'https://www.instagram.com/masarpay/'},
                       {'id': 'x', 'icon': 'fa fa-twitter', 'label': 'X', 'href': 'https://x.com/masarpay'},
                       {'id': 'youtube', 'icon': 'fa fa-youtube', 'label': 'YouTube', 'href': 'https://www.youtube.com/@MsarPay'}],
            'columns': [{'id': 'services',
                         'title': 'Services',
                         'links': [{'label': 'Payment Gateway', 'href': '/solutions#gateway'},
                                   {'label': 'POS Solutions', 'href': '/solutions#pos'},
                                   {'label': 'Accounts & Cards', 'href': '/solutions#accounts'},
                                   {'label': 'Bulk Payments', 'href': '/solutions#bulk'},
                                   {'label': 'Bill Payments', 'href': '/solutions#bills'},
                                   {'label': 'ATMs & Cash', 'href': '/solutions#atm'}]},
                        {'id': 'individuals',
                         'title': 'Individuals',
                         'links': [{'label': 'Top Up', 'href': '/individuals#topup'},
                                   {'label': 'Transfer', 'href': '/individuals#transfer'},
                                   {'label': 'Bills', 'href': '/individuals#bills'},
                                   {'label': 'Cards', 'href': '/individuals#cards'}]},
                        {'id': 'businesses',
                         'title': 'Businesses',
                         'links': [{'label': 'Solutions', 'href': '/business#solutions'},
                                   {'label': 'Sectors', 'href': '/business#sectors'},
                                   {'label': 'Developers', 'href': '/developers'},
                                   {'label': 'Partnerships', 'href': '/business#partnerships'}]},
                        {'id': 'company',
                         'title': 'Company',
                         'links': [{'label': 'About Us', 'href': '/about'},
                                   {'label': 'Vision', 'href': '/about#vision'},
                                   {'label': 'Mission & Values', 'href': '/about#mission'},
                                   {'label': 'Leadership & Governance', 'href': '/leadership'},
                                   {'label': 'Careers', 'href': '/careers'},
                                   {'label': 'News', 'href': '/news'}]},
                        {'id': 'support',
                         'title': 'Support',
                         'links': [{'label': 'Help Center', 'href': '/support'},
                                   {'label': 'FAQs', 'href': '/support#faq'},
                                   {'label': 'Complaints', 'href': '/support#complaints'},
                                   {'label': 'Technical Support', 'href': '/support#technical'}]}],
            'legal_links': [{'label': 'Privacy Policy', 'href': '/privacy'},
                            {'label': 'Website Terms', 'href': '/website-terms'},
                            {'label': 'Cookie Policy', 'href': '/cookie-policy'},
                            {'label': 'Security & Compliance', 'href': '/security-compliance'}]},
 'pages': {'about': {'seo_title': 'About Us | MASAR Pay',
                     'seo_description': 'Meet MASAR Pay, a Yemeni payment technologies and services company, '
                                        'and explore our vision, mission, and values.',
                     'hero': {'eyebrow': 'About',
                              'title': 'From Yemen, for More Connected Payments',
                              'lead': 'MASAR Pay is a Yemeni company specialising in payment technologies '
                                      'and services, operating as a payment service provider and payment '
                                      'system operator. We connect people and businesses with payment '
                                      'channels through integration with banks, digital wallets, and '
                                      'financial and technology institutions.'},
                     'blocks': [{'type': 'prose',
                                 'anchor': 'story',
                                 'title': 'Who We Are',
                                 'lead': '',
                                 'image': 'about-headquarters.webp',
                                 'image_alt': 'MASAR Pay headquarters on the Yemeni coast',
                                 'paragraphs': ['MASAR Pay is a Yemeni company specialising in payment '
                                                'technologies and services, operating as a payment service '
                                                'provider and payment system operator. We connect people and '
                                                'businesses with payment channels through integration with '
                                                'banks, digital wallets, and financial and technology '
                                                'institutions.',
                                                'We believe simpler payments start by connecting '
                                                'participants and channels and creating clarity for both '
                                                'payers and recipients.']},
                                {'type': 'prose',
                                 'anchor': 'mission',
                                 'icon': 'mission',
                                 'title': 'Our Mission',
                                 'lead': '',
                                 'paragraphs': ['To build secure, scalable payment and acceptance solutions '
                                                'that connect people and businesses with Yemen’s payment '
                                                'ecosystem and simplify how transactions are made and '
                                                'managed.']},
                                {'type': 'prose',
                                 'anchor': 'vision',
                                 'icon': 'vision',
                                 'title': 'Our Vision',
                                 'lead': '',
                                 'paragraphs': ['To make payments in Yemen more connected, accessible, and '
                                                'effortless.']},
                                {'type': 'cards',
                                 'anchor': 'values',
                                 'icon': 'values',
                                 'title': 'Our values',
                                 'lead': 'The principles behind the platform.',
                                 'items': [{'anchor': '',
                                            'icon': 'shield',
                                            'title': 'Trust',
                                            'text': 'Clear information and commitments, with responsibility '
                                                    'towards customers and partners.',
                                            'points': []},
                                           {'anchor': '',
                                            'icon': 'bulk',
                                            'title': 'Integration',
                                            'text': 'Relationships and solutions that help participants work '
                                                    'together.',
                                            'points': []},
                                           {'anchor': '',
                                            'icon': 'bolt',
                                            'title': 'Innovation',
                                            'text': 'Practical improvement guided by user needs and '
                                                    'measurable usefulness.',
                                            'points': []},
                                           {'anchor': '',
                                            'icon': 'heart',
                                            'title': 'Social Responsibility',
                                            'text': 'Wider access to digital payments and economic '
                                                    'participation.',
                                            'points': []}]},
                                {'type': 'prose',
                                 'anchor': 'management',
                                 'title': 'Leadership and Governance',
                                 'lead': '',
                                 'paragraphs': ['Governance relies on clear roles and authority, sound '
                                                'information, decision follow-up, and accountability. '
                                                'Explore our institutional approach and Chairman’s message '
                                                'on the Leadership and Governance page.']},
                                {'type': 'prose',
                                 'anchor': 'careers',
                                 'title': 'Careers at MASAR',
                                 'lead': '',
                                 'paragraphs': ['We value expertise, responsibility, and a willingness to '
                                                'learn. Visit Careers to explore work areas and application '
                                                'information.']},
                                {'type': 'prose',
                                 'anchor': 'partnerships',
                                 'title': 'Partnership at the Heart of Our Work',
                                 'lead': '',
                                 'paragraphs': ['Better payments require cooperation between banks, digital '
                                                'wallets, payment networks, and financial and technology '
                                                'institutions. We work towards relationships that create '
                                                'shared value and broaden customer choice.']},
                                {'type': 'prose',
                                 'anchor': 'journey',
                                 'title': 'Our Approach',
                                 'lead': '',
                                 'paragraphs': ['Understand the need, define the solution, review '
                                                'requirements, test readiness, and improve through use and '
                                                'feedback.']}]},
           'services': {'seo_title': 'Payment Services for People and Businesses | MASAR Pay',
                        'seo_description': 'Explore payment acceptance, account, payout, and bill payment '
                                           'solutions, including their uses, features, and onboarding '
                                           'requirements.',
                        'hero': {'eyebrow': 'Services',
                                 'title': 'Find the Service That Fits Your Needs',
                                 'lead': 'Explore payment acceptance, account, payout, and bill payment '
                                         'solutions, including their uses, features, and onboarding '
                                         'requirements.'},
                        'blocks': [{'type': 'cards',
                                    'anchor': 'catalog',
                                    'title': 'MASAR Services',
                                    'lead': 'Service availability, payment methods, fees, and limits depend '
                                            'on the product, customer eligibility, and connected channels. '
                                            'Available options and applicable terms are explained before '
                                            'subscription or activation.',
                                    'items': [{'anchor': 'gateway',
                                               'image': 'gateway',
                                               'title': 'Payment Gateway',
                                               'text': 'Connect your website and app with supported payment '
                                                       'methods and track payments linked to customer '
                                                       'orders.',
                                               'points': []},
                                              {'anchor': 'pos',
                                               'image': 'pos',
                                               'title': 'POS Solutions',
                                               'text': 'Explore payment acceptance in store and at the point '
                                                       'of service.',
                                               'points': []},
                                              {'anchor': 'accounts',
                                               'image': 'accounts',
                                               'title': 'Accounts & Cards',
                                               'text': 'Solutions for managing balances, payments, and '
                                                       'spending.',
                                               'points': []},
                                              {'anchor': 'bulk',
                                               'image': 'bulk',
                                               'title': 'Bulk Payments',
                                               'text': 'Organise payroll and other payouts to multiple '
                                                       'recipients and track results.',
                                               'points': []},
                                              {'anchor': 'bills',
                                               'image': 'bills',
                                               'title': 'Bill Payments',
                                               'text': 'Pay connected providers and keep track of your bill '
                                                       'payments.',
                                               'points': []},
                                              {'anchor': 'atm',
                                               'image': 'atm',
                                               'title': 'ATMs & Cash',
                                               'text': 'Explore available withdrawal, deposit, and service '
                                                       'locations.',
                                               'points': []}]},
                                   {'type': 'prose',
                                    'anchor': 'service-journey',
                                    'title': 'How to Get Started',
                                    'lead': '',
                                    'paragraphs': ['Tell us what you need, then review the requirements, '
                                                   'solution, and terms. Onboarding, setup, and testing are '
                                                   'completed before activation approval.',
                                                   'Service availability, payment methods, fees, and limits '
                                                   'depend on the product, customer eligibility, and '
                                                   'connected channels. Available options and applicable '
                                                   'terms are explained before subscription or activation.']},
                                   {'type': 'prose',
                                    'anchor': 'pos-scope',
                                    'title': 'POS: Acceptance That Fits How You Work',
                                    'lead': '',
                                    'paragraphs': ['Acceptance options for stores and field teams, including '
                                                   'terminals and supported mobile solutions where '
                                                   'available.',
                                                   'POS, SoftPOS, and compatible-device availability are '
                                                   'confirmed in your business offering.']},
                                   {'type': 'prose',
                                    'anchor': 'gateway-details',
                                    'title': 'Connect checkout with payment',
                                    'lead': 'Help customers complete payments on your website or app and '
                                            'link transaction results to their orders.',
                                    'paragraphs': ['Who is it for? Online stores, apps, service and booking '
                                                   'platforms, and organisations collecting payments online.',
                                                   'Use cases: Collect an online order payment, complete a '
                                                   'booking payment in an app, or collect a remote payment '
                                                   'through an enabled channel.',
                                                   'Getting started: Submit business details, review '
                                                   'requirements and integration options, complete the '
                                                   'agreement and testing, then activate after readiness '
                                                   'approval.',
                                                   'Requirements: Business and authorised representative '
                                                   'details, verification documents, website or app '
                                                   'information, products and services, and settlement '
                                                   'details.']},
                                   {'type': 'faq',
                                    'anchor': 'gateway-faq',
                                    'title': 'Questions about Payment Gateway',
                                    'lead': '',
                                    'items': [{'q': 'Which payment methods can I accept?',
                                               'a': 'Available methods depend on your business and enabled '
                                                    'integrations and are confirmed before subscription.'},
                                              {'q': 'Do I need a developer?',
                                               'a': 'This depends on the integration method. Technical '
                                                    'requirements and available options are explained during '
                                                    'the request review.'},
                                              {'q': 'When will I receive funds?',
                                               'a': 'Settlement follows the agreed schedule, payment method, '
                                                    'business days, and any applicable review.'},
                                              {'q': 'Can payments be refunded?',
                                               'a': 'Refunds depend on transaction eligibility, the payment '
                                                    'method, and applicable terms.'}]},
                                   {'type': 'prose',
                                    'anchor': 'pos-details',
                                    'title': 'Accept payments where you do business',
                                    'lead': 'Acceptance options for stores and field teams, including '
                                            'terminals and supported mobile solutions where available.',
                                    'paragraphs': ['Who is it for? Retailers, restaurants, cafés, hotels, '
                                                   'service centres, and field businesses.',
                                                   'Use cases: Take checkout payments, collect payment at '
                                                   'the customer’s location, or monitor acceptance across '
                                                   'branches.',
                                                   'Getting started: Define your business, locations, and '
                                                   'acceptance points, review the solution and connectivity '
                                                   'requirements, complete onboarding, then prepare, train, '
                                                   'and activate.',
                                                   'Requirements: Business and branch information, '
                                                   'verification documents, settlement details, device or '
                                                   'user counts, and connectivity requirements.']},
                                   {'type': 'faq',
                                    'anchor': 'pos-faq',
                                    'title': 'Questions about POS Solutions',
                                    'lead': '',
                                    'items': [{'q': 'What is the difference between POS and SoftPOS?',
                                               'a': 'POS uses a dedicated terminal. SoftPOS accepts '
                                                    'contactless payments through software on a compatible '
                                                    'phone.'},
                                              {'q': 'Does mobile acceptance work on any phone?',
                                               'a': 'No. Compatibility depends on the operating system, '
                                                    'device, security features, and solution requirements.'},
                                              {'q': 'Can I accept payments away from my store?',
                                               'a': 'This depends on the device or app, connectivity, and '
                                                    'approved usage scope.'},
                                              {'q': 'Are all cards and wallets accepted?',
                                               'a': 'Supported payment methods are specified in the service '
                                                    'offering.'}]},
                                   {'type': 'prose',
                                    'anchor': 'accounts-details',
                                    'title': 'More clarity over your balance and spending',
                                    'lead': 'Explore payment accounts and cards, including funding, usage, '
                                            'and transaction tracking for each product.',
                                    'paragraphs': ['Who is it for? Individuals organising their payments, '
                                                   'customers exploring prepaid cards, and businesses '
                                                   'eligible for expense products.',
                                                   'Use cases: Organise a payment budget, allocate funds for '
                                                   'spending, and track purchases or business expenses where '
                                                   'the relevant product is available.',
                                                   'Getting started: Choose a product, review eligibility, '
                                                   'fees, and limits, complete identity verification, then '
                                                   'follow activation and usage instructions.',
                                                   'Requirements: Identity and contact information and '
                                                   'required verification details. Eligibility and minimum '
                                                   'age depend on the product.']},
                                   {'type': 'faq',
                                    'anchor': 'accounts-faq',
                                    'title': 'Questions about Accounts & Cards',
                                    'lead': '',
                                    'items': [{'q': 'Is a payment account a bank account?',
                                               'a': 'Do not assume so. The product agreement defines the '
                                                    'account and supported services.'},
                                              {'q': 'Does a prepaid card provide credit?',
                                               'a': 'A prepaid card uses available funds and does not imply '
                                                    'a loan or credit facility.'},
                                              {'q': 'Can I use the card outside Yemen?',
                                               'a': 'This depends on the product, acceptance network, and '
                                                    'applicable restrictions.'},
                                              {'q': 'What if my card is lost?',
                                               'a': 'Use the approved blocking option where available and '
                                                    'contact official support immediately.'}]},
                                   {'type': 'prose',
                                    'anchor': 'bulk-details',
                                    'title': 'Organise payroll and other payouts',
                                    'lead': 'Prepare, review, and monitor payouts through channels and '
                                            'features enabled for your organisation.',
                                    'paragraphs': ['Who is it for? Employers and organisations paying '
                                                   'employees, suppliers, and contractors.',
                                                   'Use cases: Pay salaries, supplier invoices, and '
                                                   'contractor or other eligible recipient payments.',
                                                   'Getting started: Define payout purpose and volume, '
                                                   'review channels and funding, organise data and '
                                                   'permissions, then test and activate.',
                                                   'Requirements: Organisation and authorised representative '
                                                   'details, payout purpose, funding source, recipient '
                                                   'information, and expected volume.']},
                                   {'type': 'faq',
                                    'anchor': 'bulk-faq',
                                    'title': 'Questions about Bulk Payments',
                                    'lead': '',
                                    'items': [{'q': 'Does every recipient need a MASAR account?',
                                               'a': 'This depends on the enabled payout channel and its '
                                                    'requirements.'},
                                              {'q': 'Can I upload a payment file?',
                                               'a': 'File formats and entry methods are defined during '
                                                    'service setup.'},
                                              {'q': 'What happens if a payment fails?',
                                               'a': 'Its status is reviewed before retrying to avoid '
                                                    'duplicate payment.'},
                                              {'q': 'Can preparation and approval be separated?',
                                               'a': 'This depends on available permissions and approval '
                                                    'levels.'}]},
                                   {'type': 'prose',
                                    'anchor': 'bills-details',
                                    'title': 'Pay bills and track the outcome',
                                    'lead': 'Explore available billers, review bill details before '
                                            'confirmation, and keep the transaction reference.',
                                    'paragraphs': ['Who is it for? Individuals and businesses paying bills, '
                                                   'and billers exploring collection integration.',
                                                   'Use cases: Pay personal or business bills, or explore '
                                                   'connecting a biller to collection channels.',
                                                   'Getting started: Choose the biller, enter account or '
                                                   'bill details, review the amount and fees, then confirm '
                                                   'and retain the reference.',
                                                   'Requirements: Bill or subscriber account reference, a '
                                                   'supported payment method, and information required by '
                                                   'the provider.']},
                                   {'type': 'faq',
                                    'anchor': 'bills-faq',
                                    'title': 'Questions about Bill Payments',
                                    'lead': '',
                                    'items': [{'q': 'Which bills can I pay?',
                                               'a': 'Bills from providers listed as available in the '
                                                    'service.'},
                                              {'q': 'Will the amount appear automatically?',
                                               'a': 'Where bill enquiry is supported; other services may '
                                                    'require you to enter it.'},
                                              {'q': 'Money was debited but the bill still appears unpaid. '
                                                    'What should I do?',
                                               'a': 'Check the status, keep the reference, and contact '
                                                    'support before paying again.'},
                                              {'q': 'Can I cancel a bill payment?',
                                               'a': 'This depends on transaction status and the biller’s '
                                                    'policy. Cancellation after execution is not '
                                                    'guaranteed.'}]},
                                   {'type': 'prose',
                                    'anchor': 'atm-details',
                                    'title': 'Connecting cash and digital payments',
                                    'lead': 'Explore withdrawal and deposit channels supporting MASAR '
                                            'products and their requirements.',
                                    'paragraphs': ['Who is it for? Customers who need to withdraw funds or '
                                                   'deposit cash through approved channels.',
                                                   'Use cases: Withdraw or deposit cash through eligible '
                                                   'channels and follow up on transactions when needed.',
                                                   'Getting started: Check channel compatibility, review '
                                                   'fees and limits, follow instructions, and keep the '
                                                   'receipt and check your balance.',
                                                   'Requirements: An eligible account or card and '
                                                   'channel-specific verification requirements within '
                                                   'applicable limits.']},
                                   {'type': 'faq',
                                    'anchor': 'atm-faq',
                                    'title': 'Questions about ATMs & Cash',
                                    'lead': '',
                                    'items': [{'q': 'Can I use any ATM?',
                                               'a': 'This depends on the card and acceptance network. The '
                                                    'ATM operator may charge additional fees.'},
                                              {'q': 'Are deposits available at every location?',
                                               'a': 'Services vary by location.'},
                                              {'q': 'What are withdrawal and deposit limits?',
                                               'a': 'Limits depend on the product, channel, and verification '
                                                    'level.'},
                                              {'q': 'My account was debited but no cash was dispensed. What '
                                                    'should I do?',
                                               'a': 'Keep the time, ATM location, and transaction reference, '
                                                    'and contact official support.'}]}]},
           'business': {'seo_title': 'For Businesses | MASAR Pay',
                        'seo_description': 'Whether you run a store, digital platform, or multiple branches, '
                                           'explore acceptance, payout, and operational solutions for your '
                                           'business.',
                        'hero': {'eyebrow': 'Businesses',
                                 'title': 'Payments That Fit How You Work',
                                 'lead': 'Whether you run a store, digital platform, or multiple branches, '
                                         'explore acceptance, payout, and operational solutions for your '
                                         'business.'},
                        'blocks': [{'type': 'cards',
                                    'anchor': 'solutions',
                                    'icon': 'manage',
                                    'title': 'Solutions for Your Business Needs',
                                    'lead': '',
                                    'items': [{'anchor': '',
                                               'icon': 'card',
                                               'title': 'Accept Payments',
                                               'text': 'Choose channels that fit your customers: web, app, '
                                                       'POS, or supported field acceptance.',
                                               'points': []},
                                              {'anchor': '',
                                               'icon': 'manage',
                                               'title': 'Manage Operations',
                                               'text': 'Track payment outcomes, amounts, settlements, and '
                                                       'items needing review.',
                                               'points': []},
                                              {'anchor': '',
                                               'icon': 'chart',
                                               'title': 'Financial Review',
                                               'text': 'Explore reporting that helps your team review fees '
                                                       'and reconcile payments.',
                                               'points': []},
                                              {'anchor': '',
                                               'icon': 'scale',
                                               'title': 'Connect Your Systems',
                                               'text': 'Discuss integration for your website, app, or '
                                                       'business systems.',
                                               'points': []}]},
                                   {'type': 'cards',
                                    'anchor': 'sectors',
                                    'icon': 'store',
                                    'title': 'Sectors',
                                    'lead': 'Solutions shaped around where you sell and how you deliver '
                                            'services.',
                                    'items': [{'anchor': '',
                                               'icon': 'store',
                                               'title': 'Retail',
                                               'text': 'Accept checkout payments and track acceptance points '
                                                       'and branches.',
                                               'points': []},
                                              {'anchor': '',
                                               'icon': 'globe',
                                               'title': 'E-commerce',
                                               'text': 'Link payments to orders and monitor outcomes.',
                                               'points': []},
                                              {'anchor': '',
                                               'icon': 'building',
                                               'title': 'Enterprises',
                                               'text': 'Organise payroll, payables, and financial reports.',
                                               'points': []},
                                              {'anchor': '',
                                               'icon': 'api',
                                               'title': 'Platforms and Apps',
                                               'text': 'Explore payment integration within your user '
                                                       'experience.',
                                               'points': []}]},
                                   {'type': 'prose',
                                    'anchor': 'partnerships',
                                    'icon': 'handshake',
                                    'title': 'Partner to Broaden Payment Opportunities',
                                    'lead': '',
                                    'paragraphs': ['We welcome discussions with banks, wallets, payment '
                                                   'networks, technology providers, platforms, billers, and '
                                                   'eligible service networks.',
                                                   'Introduce your organisation, solution, and proposed '
                                                   'opportunity. We review customer value, integration '
                                                   'scope, responsibilities, operations, and support.']},
                                   {'type': 'prose',
                                    'anchor': 'merchant-onboarding',
                                    'icon': 'journey',
                                    'title': 'Merchant Onboarding',
                                    'lead': '',
                                    'paragraphs': ['Tell us about your business, review requirements and '
                                                   'documents, agree the solution and terms, then complete '
                                                   'setup, testing, and activation.',
                                                   'Activation timing depends on document completeness, '
                                                   'reviews, integration, and testing.']},
                                   {'type': 'prose',
                                    'anchor': 'operations',
                                    'icon': 'chart',
                                    'title': 'Operations, Fees, and Settlement',
                                    'lead': '',
                                    'paragraphs': ['Acceptance methods, reporting, and eligible refunds are '
                                                   'defined by the service scope.',
                                                   'Before contracting, review activation, subscription, and '
                                                   'transaction fees, limits, settlement schedules, and any '
                                                   'third-party charges.']},
                                   {'type': 'prose',
                                    'anchor': 'sector-fit',
                                    'icon': 'store',
                                    'title': 'More Industry Use Cases',
                                    'lead': '',
                                    'paragraphs': ['Restaurants and cafés: acceptance at suitable service '
                                                   'points. Travel and hospitality: collection for bookings '
                                                   'and services.',
                                                   'Education and training: explore fee collection linked to '
                                                   'payer references. Field services and delivery: '
                                                   'acceptance at the point of service where supported.']}]},
           'individuals': {'seo_title': 'For Individuals | MASAR Pay',
                           'seo_description': 'Explore accounts, cards, transfers, bills, and cash services '
                                              'to find what fits your needs.',
                           'hero': {'eyebrow': 'Individuals',
                                    'title': 'Solutions for Your Everyday Payments',
                                    'lead': 'Explore accounts, cards, transfers, bills, and cash services to '
                                            'find what fits your needs.'},
                           'blocks': [{'type': 'cards',
                                       'anchor': 'daily',
                                       'title': 'Everyday services',
                                       'lead': '',
                                       'items': [{'anchor': 'topup',
                                                  'title': 'Top Up',
                                                  'text': 'Explore approved funding channels, fees, and '
                                                          'limits.',
                                                  'points': []},
                                                 {'anchor': 'transfer',
                                                  'title': 'Money Transfers',
                                                  'text': 'Ask about supported transfer channels, '
                                                          'recipients, and requirements.',
                                                  'points': []},
                                                 {'anchor': 'bills',
                                                  'title': 'Bill Payments',
                                                  'text': 'Explore available billers and review details '
                                                          'before payment.',
                                                  'points': []},
                                                 {'anchor': 'cards',
                                                  'title': 'Accounts & Cards',
                                                  'text': 'Understand product features, usage, balances, and '
                                                          'transaction tracking.',
                                                  'points': []}]},
                                      {'type': 'prose',
                                       'anchor': 'availability',
                                       'title': 'Explore Available Options',
                                       'lead': '',
                                       'paragraphs': ['Service availability, payment methods, fees, and '
                                                      'limits depend on the product, customer eligibility, '
                                                      'and connected channels. Available options and '
                                                      'applicable terms are explained before subscription or '
                                                      'activation.',
                                                      'An enquiry does not open an account or activate a '
                                                      'service. Onboarding must be completed separately.']},
                                      {'type': 'prose',
                                       'anchor': 'eligibility',
                                       'title': 'Before You Subscribe',
                                       'lead': '',
                                       'paragraphs': ['Review eligibility, documents, fees, limits, usage '
                                                      'channels, and support options.',
                                                      'Never share passwords, PINs, or verification codes, '
                                                      'and verify the channel before entering '
                                                      'information.']}]},
           'developers': {'seo_title': 'Developers | MASAR Pay',
                          'seo_description': 'Share your use case so we can identify integration options, '
                                             'documentation, and available testing arrangements for your '
                                             'website or app.',
                          'hero': {'eyebrow': 'Developers',
                                   'title': 'Start Integration with Clear Requirements',
                                   'lead': 'Share your use case so we can identify integration options, '
                                           'documentation, and available testing arrangements for your '
                                           'website or app.'},
                          'blocks': [{'type': 'cards',
                                      'anchor': 'docs',
                                      'title': 'What Will We Review with Your Team?',
                                      'lead': '',
                                      'items': [{'anchor': 'api',
                                                 'title': 'Integration Scope',
                                                 'text': 'Required operations, platform, and systems '
                                                         'exchanging data.',
                                                 'points': []},
                                                {'anchor': 'auth',
                                                 'title': 'Authentication',
                                                 'text': 'Credential and access handling according to '
                                                         'approved documentation.',
                                                 'points': []},
                                                {'anchor': 'sandbox',
                                                 'title': 'Testing',
                                                 'text': 'Available test arrangements, data, and readiness '
                                                         'checks.',
                                                 'points': []},
                                                {'anchor': 'webhooks',
                                                 'title': 'Payment Notifications',
                                                 'text': 'Receiving and verifying notifications where '
                                                         'supported.',
                                                 'points': []},
                                                {'anchor': 'errors',
                                                 'title': 'Error Handling',
                                                 'text': 'Pending states, failures, and duplicate prevention '
                                                         'as documented.',
                                                 'points': []},
                                                {'anchor': 'guides',
                                                 'title': 'Integration Guidance',
                                                 'text': 'Technical paths suited to the product and your '
                                                         'technology.',
                                                 'points': []}]},
                                     {'type': 'prose',
                                      'anchor': 'integration',
                                      'title': 'From Request to Production',
                                      'lead': '',
                                      'paragraphs': ['Identify the service, platform, and expected usage. We '
                                                     'review requirements, available documentation and '
                                                     'access, testing, and activation criteria.',
                                                     'A test request does not activate financial services. '
                                                     'Production requires technical and contractual '
                                                     'requirements and readiness approval.']},
                                     {'type': 'prose',
                                      'anchor': 'api-reference',
                                      'title': 'Developer Guidance',
                                      'lead': '',
                                      'paragraphs': ['Keep credentials on the server, outside public '
                                                     'frontend code and logs.',
                                                     'Do not infer payment success from the customer '
                                                     'interface alone. Follow documented outcome '
                                                     'verification and duplicate prevention.',
                                                     'Use designated test data and do not include sensitive '
                                                     'information in support requests. Request documentation '
                                                     'through Contact Us, specifying the required '
                                                     'service.']}]},
           'support': {'seo_title': 'Support | MASAR Pay',
                       'seo_description': 'Help with onboarding, payments, settlements, accounts, cards, '
                                          'devices, integration, and complaints.',
                       'hero': {'eyebrow': 'Support',
                                'title': 'How Can We Help?',
                                'lead': 'Start with the FAQs or send your request subject and details '
                                        'through Contact Us.'},
                       'blocks': [{'type': 'faq',
                                   'anchor': 'faq',
                                   'title': 'FAQs',
                                   'lead': '',
                                   'items': [{'q': 'How do I request a service?',
                                              'a': 'Use Contact Us and include the service name and what you '
                                                   'need.'},
                                             {'q': 'How do I check a transaction?',
                                              'a': 'Check the channel you used or provide its reference '
                                                   'through official support.'},
                                             {'q': 'Should I pay again after an error?',
                                              'a': 'Check transaction and debit status first; the result may '
                                                   'still be updating.'},
                                             {'q': 'How do I follow up on a support request?',
                                              'a': 'Use the reference if one was issued or reply to the '
                                                   'related follow-up message.'},
                                             {'q': 'How do I change my details?',
                                              'a': 'Request a change through the approved channel. Identity '
                                                   'verification may be required.'},
                                             {'q': 'What if I suspect unauthorised use?',
                                              'a': 'Use available service or card blocking options and '
                                                   'contact official support immediately.'}]},
                                  {'type': 'prose',
                                   'anchor': 'complaints',
                                   'title': 'Tell Us About Your Complaint',
                                   'lead': '',
                                   'paragraphs': ['If you are dissatisfied with a service or request '
                                                  'outcome, describe what happened, when, the service, any '
                                                  'transaction or request reference, and the outcome you '
                                                  'want reviewed.',
                                                  'Use Contact Us and identify the message as a complaint. '
                                                  'Do not include unnecessary sensitive information.']},
                                  {'type': 'prose',
                                   'anchor': 'technical',
                                   'title': 'Technical Support',
                                   'lead': '',
                                   'paragraphs': ['Include the issue, environment, time, error message, and '
                                                  'available reference. Remove credentials and sensitive '
                                                  'customer information from examples and logs.']},
                                  {'type': 'prose',
                                   'anchor': 'complaints-policy',
                                   'title': 'Following Up on Requests',
                                   'lead': '',
                                   'paragraphs': ['Keep a copy of your request and available references, and '
                                                  'provide any further information through official '
                                                  'channels.',
                                                  'Handling depends on the case and parties involved. Never '
                                                  'send passwords, PINs, verification codes, or full card '
                                                  'details.']}]},
           'security': {'seo_title': 'Security & Compliance | MASAR Pay',
                        'seo_description': 'Guidance on protecting accounts and data, avoiding fraud, and '
                                           'reporting security concerns.',
                        'hero': {'eyebrow': 'Security',
                                 'title': 'Trust Starts with Responsibility and Clarity',
                                 'lead': 'Information protection, risk awareness, and responsible use are '
                                         'central to payment services.'},
                        'blocks': [{'type': 'cards',
                                    'anchor': 'controls',
                                    'title': 'Protect Your Account and Information',
                                    'lead': '',
                                    'items': [{'anchor': '',
                                               'title': 'Protect Credentials',
                                               'text': 'Use a strong, unique password and never share '
                                                       'verification codes.',
                                               'points': []},
                                              {'anchor': '',
                                               'title': 'Authorised Access',
                                               'text': 'Do not allow unauthorised parties to use your '
                                                       'account.',
                                               'points': []},
                                              {'anchor': '',
                                               'title': 'Fraud Awareness',
                                               'text': 'Verify links and anyone requesting payments or '
                                                       'information.',
                                               'points': []},
                                              {'anchor': '',
                                               'title': 'Review Activity',
                                               'text': 'Check unusual activity and retain references needed '
                                                       'for reporting.',
                                               'points': []}]},
                                   {'type': 'prose',
                                    'anchor': 'scope',
                                    'title': 'Verification and Responsible Use',
                                    'lead': '',
                                    'paragraphs': ['Services may require identity, business, and authorised '
                                                   'representative checks. Provide accurate information, '
                                                   'keep it updated, and use the service for its approved '
                                                   'purpose.']},
                                   {'type': 'prose',
                                    'anchor': 'protection',
                                    'title': 'Steps You Can Take',
                                    'lead': '',
                                    'paragraphs': ['Enable available additional protection, secure your '
                                                   'devices, and do not trust urgent transfer requests '
                                                   'merely because they mention MASAR.',
                                                   'For suspected unauthorised use, use available blocking '
                                                   'options and contact official support with a brief '
                                                   'description and transaction reference.']},
                                   {'type': 'prose',
                                    'anchor': 'report',
                                    'title': 'Report a Security Concern',
                                    'lead': '',
                                    'paragraphs': ['Send a technical description and reproduction steps '
                                                   'through Contact Us and identify it as a security '
                                                   'concern.',
                                                   'Do not access other people’s data, disrupt service, or '
                                                   'disclose sensitive information. Never send passwords or '
                                                   'secret keys.']}]},
           'privacy': {'seo_title': 'Privacy Policy | MASAR Pay',
                       'seo_description': 'How MASAR Pay collects, uses, protects, and manages personal '
                                          'data.',
                       'hero': {'eyebrow': 'Privacy',
                                'title': 'Privacy is a responsibility',
                                'lead': 'We explain what data we collect, why we use it, and how we protect '
                                        'it.'},
                       'blocks': [{'type': 'prose',
                                   'anchor': 'policy',
                                   'title': 'Privacy Policy',
                                   'lead': 'Last updated: 27 September 2026',
                                   'paragraphs': ['We may collect identity, contact, usage, device, and '
                                                  'transaction-related data when you use our websites and '
                                                  'services or contact us.',
                                                  'We use data to deliver and secure services, verify '
                                                  'identity, process requests, meet legal obligations, and '
                                                  'improve the experience. We do not sell personal data.',
                                                  'We may share data as necessary with service providers, '
                                                  'regulators, legal authorities, or parties authorised by '
                                                  'the customer.',
                                                  'We retain data for the period required by its purpose and '
                                                  'applicable obligations, and use appropriate technical and '
                                                  'organisational safeguards. Contact us to request access, '
                                                  'correction, or further information.']},
                                  {'type': 'prose',
                                   'anchor': 'terms',
                                   'title': 'Website Terms of Use',
                                   'lead': 'Last updated: 27 September 2026',
                                   'paragraphs': ['By using this website, you agree to use it lawfully and '
                                                  'not disrupt it or attempt unauthorised access to its '
                                                  'systems.',
                                                  'Content, trademarks, and visual assets are owned by or '
                                                  'licensed to MASAR Pay and may not be copied or reused '
                                                  'without permission.',
                                                  'Financial services are governed by separate agreements '
                                                  'presented when you subscribe. We may update these terms '
                                                  'when necessary.']},
                                  {'type': 'prose',
                                   'anchor': 'cookies',
                                   'title': 'Cookie Policy',
                                   'lead': '',
                                   'paragraphs': ['We use essential cookies for security, sessions, '
                                                  'language, and forms. If non-essential analytics or '
                                                  'marketing are introduced, we will offer clear choices '
                                                  'where required.',
                                                  'You can manage cookies in your browser, though blocking '
                                                  'essential cookies may affect some features.']}]},
           'contact': {'seo_title': 'Contact Us | MASAR Pay',
                       'seo_description': 'Contact MASAR about services, integration, partnership, or '
                                          'support.',
                       'hero': {'eyebrow': 'Contact us',
                                'title': 'Contact the MASAR Team',
                                'lead': 'Include your request subject and key details so we can route it to '
                                        'the right team.'},
                       'blocks': [{'type': 'prose',
                                   'anchor': 'contact',
                                   'title': 'How Can We Help?',
                                   'lead': '',
                                   'paragraphs': ['State the service or enquiry and how we can contact you. '
                                                  'For complaints or support, include a transaction '
                                                  'reference if available.',
                                                  'Never send passwords, PINs, verification codes, or full '
                                                  'card details.']}]},
           'terms': {'seo_title': 'Website Terms | MASAR Pay',
                     'seo_description': 'Terms governing use of the public MASAR Pay website.',
                     'hero': {'eyebrow': 'Terms',
                              'title': 'Website Terms of Use',
                              'lead': 'These terms govern this public website and do not replace product or '
                                      'service agreements.'},
                     'blocks': [{'type': 'prose',
                                 'anchor': 'terms',
                                 'title': 'Acceptable use',
                                 'lead': 'Last updated: 27 September 2026',
                                 'paragraphs': ['By using this website, you agree to use it lawfully and not '
                                                'disrupt it or attempt unauthorised access to its systems.',
                                                'Content, trademarks, and visual assets are owned by or '
                                                'licensed to MASAR Pay and may not be copied or reused '
                                                'without permission.',
                                                'Information may change and parts of the website may be '
                                                'temporarily unavailable for maintenance. Financial services '
                                                'are governed by separate agreements presented when you '
                                                'subscribe.',
                                                'We may update these terms; the latest revision date appears '
                                                'on this page.']}]},
           'cookies': {'seo_title': 'Cookie Policy | MASAR Pay',
                       'seo_description': 'How essential cookies and privacy choices work on the MASAR Pay '
                                          'website.',
                       'hero': {'eyebrow': 'Cookies',
                                'title': 'Clear choices, better privacy',
                                'lead': 'We use essential files to operate the website and do not enable '
                                        'non-essential measurement or marketing without an appropriate '
                                        'basis.'},
                       'blocks': [{'type': 'prose',
                                   'anchor': 'cookies',
                                   'title': 'How cookies are used',
                                   'lead': 'Last updated: 27 September 2026',
                                   'paragraphs': ['Essential cookies support security, session management, '
                                                  'language selection, and forms. They may be required for '
                                                  'the service to function.',
                                                  'If non-essential analytics or marketing tools are '
                                                  'introduced, we will provide a clear accept or reject '
                                                  'choice before activation where required.',
                                                  'You can manage cookies in your browser settings, although '
                                                  'blocking essential cookies may affect some features.']}]},
           'leadership': {'seo_title': 'Leadership & Governance | MASAR Pay',
                          'seo_description': "Leadership, governance, and the Chairman's message at MASAR "
                                             'Pay.',
                          'hero': {'eyebrow': 'Leadership',
                                   'title': 'Accountability and a Vision for the Future',
                                   'lead': 'Governance built on clear roles, authority, sound information, '
                                           'and decision follow-up.'},
                          'blocks': [{'type': 'prose',
                                      'anchor': 'chairman',
                                      'title': 'Chairman’s Message',
                                      'lead': 'Towards a Payment Ecosystem That Serves Yemen and Opens '
                                              'Opportunities',
                                      'paragraphs': ['In the name of God, the Most Gracious, the Most '
                                                     'Merciful.',
                                                     'The world is rapidly changing how people pay and '
                                                     'manage money. Digital payments are becoming essential '
                                                     'to everyday life and business growth. In Yemen, this '
                                                     'creates an opportunity for a more connected ecosystem '
                                                     'that responds to market needs and broadens economic '
                                                     'participation.',
                                                     'MASAR began with this national vision: to simplify '
                                                     'payments and bring financial solutions closer to their '
                                                     'users, connecting people and businesses with payment '
                                                     'channels and making transactions easier to understand '
                                                     'and manage.',
                                                     'We believe progress depends on integration and '
                                                     'partnership. Banks, digital wallets, payment networks, '
                                                     'and financial and technology institutions share a role '
                                                     'in improving the experience, widening customer choice, '
                                                     'and helping businesses accept and track payments.',
                                                     'Our success is tied to the success of our partners, '
                                                     'the value we bring merchants, the experience we offer '
                                                     'customers, and our ability to fulfil commitments '
                                                     'responsibly and consistently.',
                                                     'We pursue this ambition with a clear sense of '
                                                     'responsibility. Governance, risk management, and '
                                                     'information protection guide how we develop our '
                                                     'business and build a knowledgeable, disciplined team '
                                                     'committed to improvement.',
                                                     'We look forward to contributing to a more connected '
                                                     'and inclusive Yemeni economy and becoming a trusted '
                                                     'partner on that journey. Together, from Yemen to '
                                                     'greater opportunities.']},
                                     {'type': 'prose',
                                      'anchor': 'governance',
                                      'title': 'Governance',
                                      'lead': '',
                                      'paragraphs': ['The Board guides strategy and oversees performance and '
                                                     'risk within its authority and governing documents.',
                                                     'Executive management leads operations and delivery, '
                                                     'monitoring service quality, teams, and commitments.',
                                                     'Committees support the Board within approved mandates, '
                                                     'while control and risk functions support review and '
                                                     'remediation.']}]},
           'careers': {'seo_title': 'Careers | MASAR Pay',
                       'seo_description': 'We value expertise, responsibility, learning, and work that makes '
                                          'life and business easier for customers.',
                       'hero': {'eyebrow': 'Careers',
                                'title': 'Help Shape the Future of Payments in Yemen',
                                'lead': 'We value expertise, responsibility, learning, and work that makes '
                                        'life and business easier for customers.'},
                       'blocks': [{'type': 'prose',
                                   'anchor': 'culture',
                                   'title': 'Working at MASAR',
                                   'lead': '',
                                   'paragraphs': ['We value quality work, respect for customers and '
                                                  'colleagues, information protection, collaboration, and '
                                                  'continuous improvement.',
                                                  'Work areas include technology, product, operations, '
                                                  'customer service, business development, finance, risk, '
                                                  'compliance, and support functions.']},
                                  {'type': 'prose',
                                   'anchor': 'process',
                                   'title': 'Opportunities and Applications',
                                   'lead': '',
                                   'paragraphs': ['Review the role, location, requirements, and application '
                                                  'method in each official vacancy announcement. To enquire, '
                                                  'include your professional area through Contact Us.',
                                                  'Provide accurate professional information and avoid '
                                                  'unnecessary personal documents or financial data. CV '
                                                  'submission instructions are provided when discussing a '
                                                  'suitable opportunity.']}]},
           'news': {'seo_title': 'Newsroom | MASAR Pay',
                    'seo_description': 'Company announcements, service updates, and practical guidance to '
                                       'help you understand payment solutions.',
                    'hero': {'eyebrow': 'Newsroom',
                             'title': 'MASAR Updates and Payment Knowledge',
                             'lead': 'Company announcements, service updates, and practical guidance to help '
                                     'you understand payment solutions.'},
                    'blocks': [{'type': 'prose',
                                'anchor': 'updates',
                                'title': 'Official Announcements',
                                'lead': '',
                                'paragraphs': ['News, partnerships, and service updates are added when '
                                               'officially announced.']},
                               {'type': 'prose',
                                'anchor': 'media',
                                'title': 'Media Enquiries',
                                'lead': '',
                                'paragraphs': ['For media enquiries or company materials, contact us with '
                                               'your organisation, request subject, and contact details.']},
                               {'type': 'prose',
                                'anchor': 'gateway-or-pos',
                                'title': 'Payment Gateway or POS?',
                                'lead': '',
                                'paragraphs': ['For purchases on a website or app, explore a payment '
                                               'gateway. For payments in store or at the point of service, '
                                               'explore in-person acceptance.',
                                               'Your business may need both. Identify payment methods, '
                                               'acceptance points, order matching, reporting, and settlement '
                                               'needs.']},
                               {'type': 'prose',
                                'anchor': 'payment-followup',
                                'title': 'How to Follow Up on an Unclear Payment',
                                'lead': '',
                                'paragraphs': ['Do not start with another payment attempt. Check the '
                                               'transaction and debit status and keep the order or payment '
                                               'reference and time.',
                                               'If the outcome remains unclear, contact the channel used for '
                                               'payment. Never send a PIN, verification code, or full card '
                                               'details.']},
                               {'type': 'prose',
                                'anchor': 'before-subscription',
                                'title': 'What to Check Before Signing Up',
                                'lead': '',
                                'paragraphs': ['Review business fit, payment methods, fees, limits, '
                                               'settlement schedules, integration, and support.',
                                               'Ask what the offer includes, what needs extra setup, and '
                                               'what is actually available before signing.']}]},
           'status': {'seo_title': 'System Status | MASAR Pay',
                      'seo_description': 'MASAR Pay service availability and incident communication.',
                      'hero': {'eyebrow': 'Service status',
                               'title': 'Service Status',
                               'lead': 'Information about operational updates and how to report an issue.'},
                      'blocks': [{'type': 'prose',
                                  'anchor': 'availability',
                                  'title': 'Operational Information',
                                  'lead': '',
                                  'paragraphs': ['This page does not currently display live operational '
                                                 'monitoring. If you encounter an issue, contact support '
                                                 'with a transaction reference where available.',
                                                 'Check transaction status before paying again, and never '
                                                 'share passwords or verification codes.']}]}},
 'contact_form': {'intro': 'Include the service or enquiry and key details. Never send passwords, PINs, '
                           'verification codes, or full card details.',
                  'name': 'Full name',
                  'phone': 'Phone number',
                  'email': 'Email address',
                  'company': 'Company — optional',
                  'subject': 'Request subject',
                  'message': 'Request details',
                  'submit': 'Send Request'}}
