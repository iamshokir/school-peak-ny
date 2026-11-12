# Пакет подачи — IEEE PES GM 2027 (черновик, ничего не подано)

Портал: https://submissions.mirasmart.com/PESGM2027 · срок по CFP: 13 ноября 2026 (время и часовой пояс на странице не указаны — подаём 12.11 вечером, как вы планировали).

## 1. Поля формы (копировать как есть)

**Title**
Cold-Morning Peaks from Electrified School Heating in New York State: Heat-Pump Choice, Weather-Year Risk and Short-Duration Storage

**Author**
Shokirdzhon Ismoilov — OFTO Energy Foundation, Brooklyn, NY, USA — shokir@oftoenergy.org — ORCID 0009-0008-6551-6688 — IEEE member (номер вводите сами)

**Abstract** (150 слов — лимит шаблона PES; plain text)
Heating electrification is moving New York toward a winter-peaking grid, but the share of individual building types is rarely resolved. This paper estimates the demand that the school stock of three New York counties would add on cold school mornings if all school heating used air-source heat pumps with resistance backup. A ComStock heating signature is driven by 11 winters of hourly NOAA temperature under five heat-pump cases. The added peak is 322, 392 and 49 MW (133-202 W/m2) in New York, Erie and St. Lawrence counties, 31-59% above the peak of a median winter. Heat-pump sizing and compressor lockout move the Erie peak between 330 and 521 MW. A battery that caps the peak by 10% needs 1.2-1.9 h and is used on at most 7 school days in 11 winters; a 20% cap needs 5.2 h in Erie. Planning should use multi-year weather and specify cold-climate heat-pump performance.

**Keywords / Index Terms**
Building electrification; energy storage; heat pumps; peak demand; schools  (шаблон: не более 5, по алфавиту)

**Тема / комитет** (выбрать в выпадающем списке портала; точный список я не видел):
1. рекомендую: тема про планирование / нагрузку / электрификацию (Power System Planning, Load Modeling или Distribution/Customer-side, если есть);
2. запасной вариант: Energy Storage;
3. Super Session: "Coordinating energy storage with demand and generation flexibility" (если портал спрашивает).

**Если есть поле о связанных работах / предыдущих публикациях** (английский, для формы или письма редактору):
> Two related manuscripts by the author are under review at journals and are cited as [10] and [11]. Reference [10] sizes solar-plus-storage for a single school shelter through a 72-h winter outage; reference [11] studies forecast-informed battery readiness for such shelters. This paper reuses only the heating signature and heat-pump COP curve of [10] as inputs. Its question (fleet-level added grid peak), weather record (11 winters of NOAA ISD hourly data), heat-pump sizing and lockout cases, and peak-capping storage analysis, as well as all text, figures and tables, are new and do not appear in either manuscript.

## 2. Что проверить перед вашим «да» (решаете вы)

- [ ] **Прочитать весь текст**, особенно Discussion и Conclusion (формулировки выводов — ваши).
- [x] **Шаблон PES (PG4)** — статья собрана в вашем файле шаблона, стилями шаблона. Учтены его правила: аннотация ≤ 150 слов, ≤ 5 ключевых слов по алфавиту, единицы SI (W/m², m²), «Fig. 1», минус длинным знаком, неопубликованные работы как «unpublished».
- [ ] **≤ 5 страниц**: сейчас 3,3 страницы (PDF через LibreOffice). Откройте .docx в Word и проверьте вёрстку; подавать PDF, сохранённый из Word.
- [x] **Ссылки [10], [11]** — по правилу шаблона PES: «unpublished».
- [ ] **Репозиторий** https://github.com/iamshokir/school-peak-ny указан в Data availability. Сейчас он **приватный**: рецензенты по ссылке ничего не увидят. Варианты: (а) открыть сейчас; (б) оставить приватным и открыть после принятия (ссылка в статье пока не работает для читателя); (в) заменить строку на «available from the author on request». Решаете вы.
- [ ] **AI-раскрытие** в Acknowledgment: подтвердить формулировку, убрать [AUTHOR TO CONFIRM WORDING]. Требование IEEE: https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/
- [ ] **Номинация на Best Conference Paper / Paper Forum** — по CFP назначается программой, выбора у автора нет.
- [ ] **Регистрация и доклад.** Если статью примут, нужно зарегистрироваться (один автор платит взнос) и выступить в Сан-Франциско в июле 2027. Без доклада статья не попадёт в IEEE Xplore.
- [ ] **Авторское право.** После принятия статья передаётся IEEE (copyright), её нельзя публиковать в другом месте.

## 3. Политика (кратко, со ссылками)

- PES Author's Kit, конференционные статьи: нельзя подавать работу, которая уже опубликована или на рецензии в другом месте. Опираясь на свои прежние работы, их нужно процитировать и кратко объяснить новый вклад. Лимит — 5 страниц вместе со ссылками. https://ieee-pes.org/publications/authors-kit/preparation-and-submission-of-conference-technical-papers/
- IEEE Conference Submission Policies: нужно раскрыть похожие работы (опубликованные или поданные), процитировать их и показать отличие. Переиспользованный материал помечается и цитируется. https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/
- Elsevier (статьи 4–5 на рецензии там): нельзя публиковать по сути то же исследование дважды. https://www.elsevier.support/elsevier/answer/which-uses-of-a-work-does-elsevier-view-as-a-form-of-prior-publication
- CFP PES GM 2027: https://pes-gm.org/2027-san-francisco/2027-call-for-papers/

## 4. Что переиспользовано и что новое

| Из статьи 4 (school-shelter-ny @23d8d0b) | Новое здесь |
|---|---|
| файл тепловой сигнатуры ComStock (вход, hash в vendor/) | вопрос: добавочный пик школьного фонда целого округа для сети |
| `load_remap.py` (кривая COP, без изменений, hash) | 11 зим NOAA ISD 2014–2025 (новая загрузка и обработка) |
| правило: номинал = нагрузка при T_des | случаи CC-full, Lockout, CC-hold, NEEP на уровне фонда; школьный календарь |
| — | модель срезания пика батареей, длительность, дни использования |
| — | весь текст, оба рисунка и обе таблицы |
