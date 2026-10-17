"""The simulated WhatsApp thread with the vendor: wording only. Nothing is sent anywhere.

Each message exists in English and in Hindi. The Hindi is a draft written for this prototype: a Hindi speaker at the client must review it before any real use. It translates the
frame of each message, the reader's field names, one standing line per vendor-facing check, and the status sentences of `app/tracker/status.py` (the 26 query reasons and the stage
sentences). Values inside a message (invoice numbers, dates, names) are the bill's own and are not translated.

Two things post to the thread: the message the verdict would send (built in `app.ui.data.messages`, Hindi added here), and the reply to a vendor's new photo: what was found in
plain words, then the bill status sentence from the tracker (received, checked at the property, with head office, a query with the reason and who must act, or paid on a date).

Real connection: a WhatsApp Business API account on a company number, approved message templates in each language, the vendor's recorded opt-in, and the bill files kept on the
company side. Replies would arrive by webhook as an image; here the reply is a file chosen on the card.
"""
from __future__ import annotations

from datetime import date

from app.tracker import status as tstatus
from app.tracker.ledger import Bill
from app.tracker.payruns import DEFAULT_CUTOFF_DAYS, next_run_for_open_bill

DAYS = {"Monday": "सोमवार", "Tuesday": "मंगलवार", "Wednesday": "बुधवार", "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार", "Sunday": "रविवार"}
MONTHS = {"January": "जनवरी", "February": "फ़रवरी", "March": "मार्च", "April": "अप्रैल", "May": "मई", "June": "जून", "July": "जुलाई", "August": "अगस्त",
          "September": "सितंबर", "October": "अक्टूबर", "November": "नवंबर", "December": "दिसंबर"}


def hi_date(d: date) -> str:
    return f"{DAYS[f'{d:%A}']} {d.day} {MONTHS[f'{d:%B}']} {d.year}"


NOUN = {"bill": "बिल", "credit note": "क्रेडिट नोट"}
FIELD_HI = {"Vendor": "विक्रेता का नाम", "Vendor GSTIN": "विक्रेता का GSTIN", "Invoice number": "इनवॉइस नंबर", "Invoice date": "इनवॉइस की तारीख", "Work order": "वर्क ऑर्डर",
            "Taxable value": "कर-योग्य राशि", "Total": "कुल राशि"}

# one standing line per vendor-facing check (the English fix text carries values from the bill; the Hindi line is the general ask)
FIX_HI = {
    "P1/H1": "आपके बिल पर GSTIN छपा नहीं है या हमारे रिकॉर्ड से मेल नहीं खाता। कृपया सही GSTIN के साथ बिल दोबारा भेजें, या GSTIN बदला हो तो हमें बताएँ।",
    "P3": "बिल पर वर्क ऑर्डर या पर्चेज़ ऑर्डर नंबर नहीं है, या वह हमारे पास नहीं मिला। कृपया सही नंबर के साथ बिल भेजें।",
    "H3": "वर्क ऑर्डर या बिल की तारीख साफ़ नहीं है। कृपया वर्क ऑर्डर नंबर और तारीख साफ़ दिखाते हुए बिल भेजें।",
    "H13": "इसी तारीख और राशि का बिल हमारे पास पहले से दर्ज है। अगर यह नया बिल है तो कृपया नए इनवॉइस नंबर के साथ भेजें।",
    "H11": "बिल पर HSN या SAC कोड, या GST की दर सही नहीं है। कृपया सुधरा हुआ बिल भेजें।",
    "H10": "बिल पर कर का प्रकार आपूर्ति के स्थान से मेल नहीं खाता, या कर वाला पन्ना चाहिए। कृपया सुधरा हुआ बिल भेजें।",
}

# the 26 query reasons of app/tracker/status.py: (reason, what the owner must do), in Hindi, keyed by the English reason
QUERY_HI = {
    "an invoice with the same number has already been booked": ("इसी नंबर का एक बिल पहले ही दर्ज हो चुका है", "यह पुष्टि करना कि यह नया बिल है या नहीं, और नया हो तो नए इनवॉइस नंबर के साथ भेजना"),
    "the cost centre on the entry in our system belongs to another property": ("हमारे सिस्टम की एंट्री में कॉस्ट सेंटर किसी दूसरी प्रॉपर्टी का है", "कॉस्ट सेंटर सुधारना"),
    "the accounting code on the work order does not fit this kind of expense": ("वर्क ऑर्डर पर अकाउंटिंग कोड इस तरह के खर्च से मेल नहीं खाता", "सही कोड की पुष्टि करना"),
    "the project code for this spend has been closed": ("इस खर्च का प्रोजेक्ट कोड बंद हो चुका है", "प्रोजेक्ट कोड दोबारा खुलवाना या बदलवाना"),
    "the tax type on your bill (IGST) does not fit where the service was supplied": ("आपके बिल पर कर का प्रकार (IGST) सेवा की आपूर्ति के स्थान से मेल नहीं खाता", "सही कर प्रकार के साथ सुधरा हुआ बिल भेजना"),
    "the HSN or SAC code is missing from your bill": ("आपके बिल पर HSN या SAC कोड नहीं है", "कोड के साथ सुधरा हुआ बिल भेजना"),
    "the tax rate on your bill does not look right": ("आपके बिल पर कर की दर सही नहीं लग रही", "सुधरा हुआ बिल भेजना"),
    "the GSTIN on your bill does not match the one we hold for you": ("आपके बिल का GSTIN हमारे पास दर्ज GSTIN से मेल नहीं खाता", "सुधरा हुआ बिल भेजना, या GSTIN बदला हो तो हमें बताना"),
    "the bill is on hold after a discussion with the property team": ("प्रॉपर्टी टीम से चर्चा के बाद बिल रोका गया है", "उसे जारी करना या बताना कि क्या चाहिए"),
    "the work order may not have enough balance left for this bill": ("हो सकता है वर्क ऑर्डर में इस बिल के लिए पर्याप्त राशि न बची हो", "शेष राशि जाँचना और ज़रूरत हो तो ऑर्डर बढ़ाना"),
    "the bill amount differs from the amount confirmed at the property": ("बिल की राशि प्रॉपर्टी पर पुष्ट राशि से अलग है", "राशि पर सहमत होकर एंट्री सुधारना"),
    "the purchase order has not been released": ("पर्चेज़ ऑर्डर अभी जारी नहीं हुआ है", "ऑर्डर जारी करना"),
    "the company name on your bill is wrong": ("आपके बिल पर कंपनी का नाम गलत है", "सही कंपनी नाम के साथ सुधरा हुआ बिल भेजना"),
    "only a scan has reached us and the original has not": ("हमारे पास केवल स्कैन पहुँचा है, मूल बिल नहीं", "मूल बिल हेड ऑफिस भेजना"),
    "your bank details have changed": ("आपके बैंक विवरण बदल गए हैं", "कैंसल्ड चेक भेजना"),
    "overtime is billed that the work order does not cover": ("बिल में ओवरटाइम लगाया गया है जो वर्क ऑर्डर में शामिल नहीं है", "सुधरा हुआ बिल भेजना, या सहमति हुई हो तो वर्क ऑर्डर संशोधन भेजना"),
    "the rate on your bill is higher than the work order rate": ("आपके बिल की दर वर्क ऑर्डर की दर से ज़्यादा है", "वर्क ऑर्डर की दर पर सुधरा हुआ बिल भेजना"),
    "the property has not yet confirmed receipt of the work in our system": ("प्रॉपर्टी ने अभी हमारे सिस्टम में काम की प्राप्ति की पुष्टि नहीं की है", "सर्विस एंट्री दर्ज करना"),
    "the property has not yet confirmed receipt of the goods in our system": ("प्रॉपर्टी ने अभी हमारे सिस्टम में माल की प्राप्ति की पुष्टि नहीं की है", "माल प्राप्ति (GRN) दर्ज करना"),
    "the service report is not attached": ("सर्विस रिपोर्ट संलग्न नहीं है", "हस्ताक्षरित सर्विस रिपोर्ट भेजना"),
    "the delivery challan does not carry the security gate stamp": ("डिलीवरी चालान पर सुरक्षा गेट की मुहर नहीं है", "चालान पर मुहर लगवाना"),
    "the PF and ESIC challans for last month are not attached": ("पिछले महीने के PF और ESIC चालान संलग्न नहीं हैं", "चालान भेजना"),
    "the attendance sheet has not been signed by the property head": ("हाज़िरी शीट पर प्रॉपर्टी हेड के हस्ताक्षर नहीं हैं", "हाज़िरी शीट पर हस्ताक्षर करवाना"),
    "the quantity billed is more than the work order has left": ("बिल की मात्रा वर्क ऑर्डर में बची मात्रा से ज़्यादा है", "ऑर्डर बढ़ाना या बिल घटाना"),
    "the work order has no balance left for this period": ("इस अवधि के लिए वर्क ऑर्डर में कोई राशि नहीं बची", "ऑर्डर बढ़ाना या और राशि जारी करना"),
    "the work order had expired on the date of the bill": ("बिल की तारीख को वर्क ऑर्डर की अवधि समाप्त हो चुकी थी", "वर्क ऑर्डर बढ़ाना"),
    "we are checking a detail on the bill": ("हम बिल का एक विवरण जाँच रहे हैं", "प्रश्न देखकर बताना कि किसे कार्रवाई करनी है"),
}
OWNER_HI = {"vendor": "आपको", "property": "प्रॉपर्टी टीम को", "procurement": "हमारी प्रोक्योरमेंट टीम को", "AP": "हमारी अकाउंट्स टीम को"}


def noun_of(doc_type: str | None) -> str:
    return "credit note" if doc_type == "credit_note" else "bill"


# ------------------------------------------------------------------------------------------------ the message the verdict sends (Hindi added to the English one in data.messages)
def hindi_resend(vendor: str, noun: str, inv: str | None, unread: list[str]) -> str:
    n = NOUN[noun]
    ref = f"आपके {n} {inv}" if inv else f"आपके {n}"
    if unread:
        return f"नमस्ते {vendor}, हम {ref} के ये हिस्से साफ़ नहीं पढ़ पाए: {', '.join(FIELD_HI.get(u, u) for u in unread)}। कृपया पूरे {n} की साफ़ फ़ोटो या स्कैन भेजें। धन्यवाद।"
    return f"नमस्ते {vendor}, हम {ref} को साफ़ नहीं पढ़ पाए। कृपया पूरे {n} की साफ़ फ़ोटो या स्कैन भेजें। धन्यवाद।"


def hindi_fixes(check_ids: tuple[str, ...] | list[str]) -> str:
    return " ".join(FIX_HI[c] for c in check_ids if c in FIX_HI)


def hindi_tell_vendor(vendor: str, noun: str, inv: str | None, check_ids) -> str:
    n = NOUN[noun]
    ref = f"आपके {n} {inv}" if inv else f"आपके {n}"
    return f"नमस्ते {vendor}, हमने {ref} को आते ही जाँचा। बिना देरी के भुगतान के लिए कृपया ये ठीक करें: {hindi_fixes(check_ids)} कृपया आज ही सुधरा हुआ {n} भेजें। धन्यवाद।"


def ask_resend(noun: str, unread: list[str]) -> tuple[str, str]:
    """The vendor's ask when parts could not be read, as (English, Hindi). Used inside the first message and again in the reply to a new photo."""
    n = NOUN[noun]
    if unread:
        return (f"We could not read these parts clearly: {', '.join(unread)}. Please send a clearer photo or scan of the whole {noun}.",
                f"हम ये हिस्से साफ़ नहीं पढ़ पाए: {', '.join(FIELD_HI.get(u, u) for u in unread)}। कृपया पूरे {n} की साफ़ फ़ोटो या स्कैन भेजें।")
    return (f"We could not read it clearly. Please send a clearer photo or scan of the whole {noun}.", f"हम इसे साफ़ नहीं पढ़ पाए। कृपया पूरे {n} की साफ़ फ़ोटो या स्कैन भेजें।")


def ask_fix(noun: str, text: str, check_ids) -> tuple[str, str]:
    n = NOUN[noun]
    return (f"To pay it without delay please fix: {text} Please send the corrected {noun} today.", f"बिना देरी के भुगतान के लिए कृपया ये ठीक करें: {hindi_fixes(check_ids)} कृपया आज ही सुधरा हुआ {n} भेजें।")


# ------------------------------------------------------------------------------------------------ the bill status sentence in Hindi (mirrors tstatus.vendor_sentence)
def hindi_status(b: Bill, cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> str:
    n = NOUN[noun_of(b.doc_type)]
    plain = f"{n} {b.invoice_no}"
    ref = f"आपका {plain}"
    e = b.entered
    d = lambda k: hi_date(e[k]) if e.get(k) else "एक अदर्ज तारीख"
    if b.stage == "paid":
        if "paid_before_posted" in b.flags:
            return f"{ref} का भुगतान हो गया है। भुगतान की तारीख की पुष्टि की जा रही है।"
        return f"{ref} का भुगतान {d('paid')} को हो गया।"
    q = b.open_query
    if q:
        reason, action = QUERY_HI.get(q.reason, QUERY_HI["we are checking a detail on the bill"])
        return f"{ref} रोका गया है। {hi_date(q.raised_date)} को हमने एक सवाल उठाया: {reason}। {OWNER_HI[q.owner]} {action} होगा।"
    if b.stage == "desk":
        return f"हमें {plain} {d('desk')} को मिला। प्रॉपर्टी उसकी जाँच कर रही है।"
    if b.stage == "verified":
        return f"{ref} की प्रॉपर्टी पर {d('verified')} को जाँच हुई। अब वह प्रॉपर्टी हेड के हस्ताक्षर की प्रतीक्षा में है।"
    if b.stage == "signed":
        return f"{ref} की प्रॉपर्टी पर {d('signed')} को जाँच और हस्ताक्षर हुए। वह हमारे हेड ऑफिस की ओर जा रहा है।"
    if b.stage == "received":
        return f"{ref} {d('received')} को हमारे हेड ऑफिस पहुँचा और हमारी अकाउंट्स टीम के उठाने की प्रतीक्षा में है।"
    if b.stage == "picked":
        return f"हमारी अकाउंट्स टीम ने {plain} {d('picked')} को उठाया और उसकी जाँच कर रही है।"
    if b.doc_type == "credit_note":
        return f"{ref} हमारे सिस्टम में दर्ज हो गया है।"
    run = next_run_for_open_bill(e.get("posted"), b.as_of, cutoff_days)
    return f"{ref} हमारे सिस्टम में दर्ज हो गया है। वह {hi_date(run)} के पेमेंट रन में जा सकता है। भुगतान मंगलवार और शुक्रवार को होते हैं।"


# ------------------------------------------------------------------------------------------------ the reply to a vendor's photo
def reply(res: dict, out: dict, bill: Bill | None, vendor_msgs: list[dict], cutoff_days: int = DEFAULT_CUTOFF_DAYS) -> dict:
    """The company's answer to a new photo, in plain words, as {en, hi}: what was found, what the vendor must do (if anything), then the bill status sentence from the tracker.
    `vendor_msgs` are the WhatsApp messages the new card produced (each with en `text` and `hi`); their ask is repeated here rather than a second message being sent."""
    noun = noun_of(res.get("doc_type"))
    f = res.get("fields") or {}
    inv = (f.get("invoice_no") or {}).get("value")
    ok_inv = inv if inv and float((f.get("invoice_no") or {}).get("conf", 0) or 0) >= 0.70 else None
    ref = f"your {noun} {ok_inv}" if ok_inv else f"your {noun}"
    ref_hi = f"आपका {NOUN[noun]} {ok_inv}" if ok_inv else f"आपका {NOUN[noun]}"
    en = [f"Thank you, we received {ref}."]
    hi = [f"धन्यवाद, हमें {ref_hi} मिल गया।"]
    ask = [m for m in vendor_msgs if m.get("kind") in ("resend", "tell-vendor")]
    if ask:
        for m in ask:
            en.append(m["ask"])
            hi.append(m["ask_hi"])
    elif out["routing"].route == "auto-clear":
        en.append("We checked it on arrival and nothing more is needed from you.")
        hi.append("हमने इसे आते ही जाँचा और आपसे अब और कुछ नहीं चाहिए।")
    else:
        en.append("We checked it on arrival. Nothing more is needed from you now; our team is looking at one detail.")
        hi.append("हमने इसे आते ही जाँचा। अभी आपसे और कुछ नहीं चाहिए; हमारी टीम एक विवरण देख रही है।")
    if bill is not None:
        en.append(tstatus.vendor_sentence(bill, cutoff_days))
        hi.append(hindi_status(bill, cutoff_days))
    else:
        en.append("We will tell you when it moves to the next step.")
        hi.append("अगले चरण में जाने पर हम आपको बताएँगे।")
    return dict(en=" ".join(en), hi=" ".join(hi))
