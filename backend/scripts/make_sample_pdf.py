"""Generuje eval/regulamin_studiow.pdf (fikcyjny regulamin, 4 paragrafy na stronę). Wymaga reportlab + DejaVu."""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
body = ParagraphStyle("b", fontName="DV", fontSize=10, leading=14)
head = ParagraphStyle("h", fontName="DVB", fontSize=12, leading=16, spaceBefore=10, spaceAfter=4)

S = [
("Postanowienia ogólne", "Regulamin określa organizację i tok studiów w Akademii Nauk Stosowanych w Zielonej Wsi. Studia pierwszego stopnia prowadzone są w formie stacjonarnej i niestacjonarnej. Regulamin obowiązuje wszystkich studentów od dnia immatrykulacji do dnia ukończenia studiów lub skreślenia z listy studentów."),
("Rok akademicki", "Rok akademicki dzieli się na semestr zimowy i letni. Semestr zimowy trwa od 1 października do 31 stycznia, a semestr letni od 1 lutego do 30 czerwca. Po każdym semestrze następuje sesja egzaminacyjna trwająca dwa tygodnie. Rektor może wyznaczyć dni wolne od zajęć dydaktycznych w drodze zarządzenia."),
("Prawa studenta", "Student ma prawo do kształcenia zgodnego z programem studiów, do opieki naukowej nauczycieli akademickich, do korzystania z biblioteki i infrastruktury uczelni oraz do zrzeszania się w organizacjach studenckich. Student ma prawo do wglądu w swoje prace egzaminacyjne w ciągu siedmiu dni od ogłoszenia wyników."),
("Obowiązki studenta", "Student jest obowiązany przestrzegać regulaminu, dbać o dobre imię uczelni oraz uczestniczyć w zajęciach. Student jest obowiązany niezwłocznie powiadamiać dziekanat o zmianie adresu korespondencyjnego, nazwiska lub numeru telefonu. Student zobowiązany jest do terminowego regulowania opłat określonych w zarządzeniu rektora."),
("Rekrutacja", "Zasady przyjęć na studia określa uchwała senatu podejmowana nie później niż do 30 czerwca roku poprzedzającego rok akademicki. Kandydaci rejestrują się w elektronicznym systemie rekrutacyjnym i wnoszą opłatę rekrutacyjną. Listy rankingowe publikowane są na stronie internetowej uczelni."),
("Immatrykulacja", "Immatrykulacja następuje przez złożenie ślubowania wobec rektora lub dziekana i wpisanie na listę studentów. Osoba przyjęta na studia składa w dziekanacie komplet dokumentów w terminie pięciu dni roboczych od ogłoszenia wyników rekrutacji. Niezłożenie dokumentów w terminie oznacza rezygnację z miejsca."),
("Legitymacja studencka", "Legitymacja studencka jest wydawana w ciągu 14 dni od immatrykulacji i jest ważna cztery lata, z możliwością przedłużania co semestr przez naklejenie hologramu. Za wydanie duplikatu zagubionej legitymacji pobierana jest opłata w wysokości 17 zł. Legitymacja uprawnia do ulgowych przejazdów komunikacją publiczną."),
("Organizacja zajęć", "Obecność na ćwiczeniach, laboratoriach i seminariach jest obowiązkowa. Student może mieć najwyżej dwie nieusprawiedliwione nieobecności w semestrze na jednym przedmiocie. Nieobecność usprawiedliwia się zwolnieniem lekarskim złożonym prowadzącemu w ciągu siedmiu dni od powrotu na zajęcia. Obecność na wykładach nie jest obowiązkowa, chyba że sylabus stanowi inaczej."),
("Punkty ECTS", "Za semestr studiów student może uzyskać 30 punktów ECTS, a za rok akademicki 60 punktów. Studia pierwszego stopnia trwają sześć semestrów i obejmują 180 punktów ECTS. Punkty przyznawane są za osiągnięcie efektów uczenia się, a nie za sam udział w zajęciach."),
("Zaliczenia i egzaminy", "Wyniki zaliczeń i egzaminów wyrażane są w skali ocen od 2,0 do 5,0: 2,0 niedostateczny, 3,0 dostateczny, 3,5 dostateczny plus, 4,0 dobry, 4,5 dobry plus, 5,0 bardzo dobry. Wyniki egzaminów ogłaszane są w systemie USOS w ciągu siedmiu dni od egzaminu."),
("Egzamin poprawkowy", "Student, który nie zaliczył egzaminu w pierwszym terminie, ma prawo do dwóch terminów poprawkowych. Pierwszy termin poprawkowy wyznacza się w ciągu 14 dni od zakończenia sesji. Trzeci termin ma formę egzaminu komisyjnego i jest wyznaczany na wniosek studenta skierowany do dziekana."),
("Warunkowy wpis na semestr", "Dziekan może wpisać studenta na kolejny semestr warunkowo, jeżeli brakuje mu nie więcej niż 8 punktów ECTS z poprzedniego semestru. Student zobowiązany jest uzupełnić zaległości do końca pierwszego miesiąca semestru, w przeciwnym razie warunkowy wpis wygasa."),
("Powtarzanie semestru", "Student, który nie uzyskał zaliczenia semestru, może go powtórzyć raz w całym okresie studiów. Zgodę na powtarzanie semestru wydaje dziekan, a student wnosi opłatę za powtarzane zajęcia zgodnie z zarządzeniem rektora. Powtarzanie semestru nie przedłuża łącznego limitu urlopów."),
("Urlop dziekański", "Dziekan udziela urlopu dziekańskiego na okres do dwóch semestrów w przypadku choroby, urodzenia dziecka lub ważnych okoliczności losowych. Wniosek o urlop składa się w dziekanacie najpóźniej 30 dni po rozpoczęciu semestru. W czasie urlopu student nie ma prawa uczestniczyć w zajęciach ani zaliczać przedmiotów."),
("Indywidualna organizacja studiów", "Indywidualna organizacja studiów przysługuje studentom z niepełnosprawnością, sportowcom reprezentującym uczelnię oraz studentom wychowującym dziecko. Wniosek o IOS składa się do dziekana w ciągu 14 dni od rozpoczęcia semestru. Dziekan określa zasady zaliczania przedmiotów i terminy w porozumieniu z prowadzącymi."),
("Wymiana zagraniczna", "Student może odbyć część studiów za granicą w ramach programu Erasmus+. O wyjazd mogą ubiegać się studenci, którzy ukończyli co najmniej pierwszy rok studiów, mają średnią ocen nie niższą niż 3,5 i potwierdzają znajomość języka obcego na poziomie B2. Rekrutację prowadzi Dział Współpracy Międzynarodowej."),
("Stypendium socjalne", "Stypendium socjalne przysługuje studentowi, w którego rodzinie miesięczny dochód na osobę nie przekracza 1800 zł. Wniosek wraz z zaświadczeniami o dochodach należy złożyć do 15 października w systemie USOS. Stypendium wypłacane jest co miesiąc przez okres dziewięciu miesięcy w roku akademickim."),
("Stypendium rektora", "Stypendium rektora może otrzymać student, który uzyskał wysoką średnią ocen, nie niższą niż 4,5, lub osiągnięcia naukowe, artystyczne albo sportowe. Stypendium przyznaje się nie więcej niż 10% studentów danego kierunku. Wniosek składa się do 20 października."),
("Zapomoga", "Student, który znalazł się przejściowo w trudnej sytuacji życiowej, może otrzymać zapomogę raz w semestrze w wysokości do 1500 zł. Wniosek o zapomogę składa się do komisji stypendialnej wraz z dokumentami potwierdzającymi trudną sytuację, najpóźniej w ciągu trzech miesięcy od jej zaistnienia."),
("Praca dyplomowa", "Temat pracy dyplomowej student wybiera i zatwierdza u promotora najpóźniej do końca czwartego semestru. Praca licencjacka powinna liczyć co najmniej 40 stron znormalizowanego tekstu i musi zostać sprawdzona w systemie antyplagiatowym. Pracę składa się w dziekanacie w wersji elektronicznej na 14 dni przed egzaminem dyplomowym."),
("Egzamin dyplomowy", "Egzamin dyplomowy odbywa się przed trzyosobową komisją i obejmuje obronę pracy oraz odpowiedź na pytania z zakresu kierunku. Ostateczny wynik studiów stanowi suma: 60% średniej ze studiów, 20% oceny pracy dyplomowej i 20% oceny z egzaminu dyplomowego."),
("Skreślenie z listy studentów", "Dziekan skreśla studenta z listy w przypadku niepodjęcia studiów, rezygnacji ze studiów, niezłożenia pracy dyplomowej w terminie lub nieuzyskania zaliczenia semestru po jego powtórzeniu. Od decyzji o skreśleniu przysługuje odwołanie do rektora w terminie 14 dni od jej doręczenia."),
("Odpowiedzialność dyscyplinarna", "Student ponosi odpowiedzialność dyscyplinarną za naruszenie przepisów obowiązujących na uczelni oraz za czyn uchybiający godności studenta, w tym plagiat. Komisja dyscyplinarna może orzec karę upomnienia, nagany, nagany z ostrzeżeniem, zawieszenia w prawach studenta do jednego roku albo wydalenia z uczelni."),
("Postanowienia końcowe", "W sprawach nieuregulowanych w regulaminie rozstrzyga rektor. Regulamin wchodzi w życie z dniem 1 października 2025 roku i zastępuje dotychczasowy regulamin studiów. Zmiany regulaminu wymagają uchwały senatu podjętej większością głosów."),
]
story = [Paragraph("Regulamin studiów — Akademia Nauk Stosowanych w Zielonej Wsi", head)]
for i, (t, txt) in enumerate(S, start=1):
    story += [Paragraph(f"§ {i}. {t}", head), Paragraph(txt, body)]
    if i % 4 == 0 and i != len(S):
        story.append(PageBreak())
SimpleDocTemplate(sys.argv[1] if len(sys.argv) > 1 else "eval/regulamin_studiow.pdf", pagesize=A4).build(story)
