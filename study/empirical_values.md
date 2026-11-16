# Empirical values for the simulated study (contact rates and sensor detection)

Compiled 2026-11-13. Every quote below was read in the full text of the source (PDF
converted with pdftotext, or the full-text XML from Europe PMC). Page numbers refer to
the PDF version named in each entry. For sources read as Europe PMC XML there are no
page numbers, so the section is given instead. Numbers marked "my arithmetic" are not in
the source; they are computed from quoted numbers.

Copies of all files read are in
/private/tmp/claude-502/-Users-leo-torres-research-hoi-debate/fd90344c-4f41-4446-8221-642739b779f0/scratchpad/sources/

Not read: Smieszek et al. 2014 (BMC Infect Dis 14:136) was downloaded as full-text XML
but not used, because it used TelosB motes in a US high school, not SocioPatterns
badges. Its 2016 follow-up at a conference with SocioPatterns badges (below) fits our
case better.


## Part 1. How much people are in contact

### 1a. Génois and Barrat 2018 (daily degree and largest clique, six SocioPatterns sets)

M. Génois and A. Barrat, "Can co-location be used as a proxy for face-to-face
contacts?", EPJ Data Science 7:11 (2018). Read: arXiv:1712.06346v1,
https://arxiv.org/abs/1712.06346 (the published version may differ in small ways).

Data sets, p. 3, Table 1: InVS13 (workplace, 2013, 92 participants, 2 weeks), InVS15
(workplace, 2015, 232 participants, 2 weeks), SFHH (conference, 2009, 403 participants,
2 days), and three others (hospital, primary school, high school).

p. 5, Table 3 rows for the contact network (subscript c), columns InVS13, InVS15, LH10,
LyonSchool, SFHH, Thiers13:

> k̄c 2.9 6.4 14.0 47.3 28.8 13.5

> ωc 4.4 7.6 14.3 22.5 11.0 9.4

Table 3 caption, p. 5:

> We compare the average degree (k̄) network density (ρ), clique number (ω) and average
> clustering (c̄) of daily aggregated networks, for the contact network (c subscript)
> [...] Values are averaged over all the days of the study. In the case of SFHH, since
> on the second day there was activity only during the morning, only the values of the
> first day are reported.

Plain statement: average number of distinct contacts per person per day is 2.9 and 6.4
in the two workplace data sets and 28.8 at the conference. The largest clique in a daily
network has about 4 to 8 people at the workplace and 11 at the conference. Note that the
clique number is the largest clique in the network aggregated over a day, not the size
of a group at one moment, so it overstates instantaneous group size.

### 1b. Génois et al. 2015 (office building, the InVS13 data set)

M. Génois, C. L. Vestergaard, J. Fournet, A. Panisson, I. Bonmarin, A. Barrat, "Data on
face-to-face contacts in an office building suggest a low-cost vaccination strategy
based on community linkers", Network Science 3(3):326-347 (2015). Read:
arXiv:1409.7017v2, https://arxiv.org/abs/1409.7017

p. 3, Sec. 2:

> Two thirds of the total staff agreed to participate to the data collection.

(Génois and Barrat 2018 cite this paper for InVS13. Their Table 1 lists 92 participants;
Table 1 of this paper, p. 4, gives a total of 100 of 145 staff, 69%.)

p. 5, Sec. 3.2:

> although the study lasted two weeks, the average degree in the aggregated network is
> only around 15, meaning that each individual met only ∼ 15% of the office population
> participating to the study over the course of these two weeks.

p. 7, Sec. 3.2:

> at the fastest time scale, i.e. the time resolution of 20 seconds, nodes have an
> average instantaneous degree of 0.013, and overall only 0.66 links exist on average in
> the whole network

Plain statement: in an ordinary office, a person is in a detected face-to-face contact
in about 1.3% of 20-second windows (an upper bound on the fraction of time in contact),
and meets about 15 distinct colleagues in two weeks. This is far sparser than an event.

### 1c. Stehlé et al. 2011 (SFHH conference, 2 days)

J. Stehlé, N. Voirin, A. Barrat, et al., "Simulation of an SEIR infectious disease model
on the dynamic contact network of conference attendees", BMC Medicine 9:87 (2011).
https://doi.org/10.1186/1741-7015-9-87. Read: Europe PMC full text, PMC3162551.

Methods, "Data collection in this study":

> of the 1,200 attendees, 405 volunteers wore the tags. [...] The data were collected
> from 9 am to 9 pm on the first day and from 8.30 am to 4.30 pm on the second day

Results:

> In total, 28,540 face-to-face contacts between 405 attendees at a 2-day conference
> were recorded [...] The mean duration was 49 seconds, with large variations (SD 112
> seconds)

> In the daily contact networks, the mean degree of a node was close to 30

> The link weights, by contrast, had a broad distribution, with a mean cumulated
> duration of the interaction between two attendees of 2 minutes. The total duration
> spent in contact by any attendee also had a broad distribution, with a mean of 75
> minutes.

Plain statement: at a conference, a person has about 30 distinct contacts per day. My
arithmetic: 28,540 x 2 / 405 / 2 days = about 70 contact events per person per day, and
70 x 49 s = about 58 minutes in contact per person per day, which is about 10% of a
10-hour recorded day. The paper's "mean of 75 minutes" does not say whether it is per
day or over both days; my arithmetic gives 115 minutes over both days, so I cannot
reconcile it. Treat it with care.

### 1d. Isella et al. 2011 (HT09 conference, 3 days, about 100 people)

L. Isella, J. Stehlé, A. Barrat, C. Cattuto, J.-F. Pinton, W. Van den Broeck, "What's in
a crowd? Analysis of face-to-face behavioral networks", J. Theor. Biol. 271:166-180
(2011). Read: arXiv:1006.1260v3, https://arxiv.org/abs/1006.1260

p. 2, Sec. II:

> the latter took place over the course of three days and involved about 100 conference
> participants (about 10, 000 contacts).

> at HT09, about 75% of the participants volunteered to being tracked.

p. 5, Sec. III:

> the HT09 degree distribution exhibits a peak at k around 15 − 20, pointing to a
> characteristic number of contacts established during the conference. Moreover, the
> average degree in the HT09 case, hki, close to 20

(hki is how pdftotext renders ⟨k⟩.)

> removing all the contacts with a cumulated duration below one minute yields hki about
> 7.5 for HT09

p. 7, Sec. IV:

> in both the HT09 and SG cases most of the recorded interactions amount to
> shortly-sustained contacts lasting less than one minute.

Plain statement: at a 3-day conference of our size class, a person has about 20 distinct
contacts per day, but only about 7.5 if pairs with less than one minute of total contact
are dropped. My arithmetic: 10,000 x 2 / 100 / 3 = about 67 contact events per person
per day.

### 1e. Mastrandrea et al. 2015 (high school, 5 days, for comparison)

R. Mastrandrea, J. Fournet, A. Barrat, "Contact patterns in a high school: a comparison
between data collected using wearable sensors, contact diaries and friendship surveys",
PLoS ONE 10(9):e0136497 (2015). https://doi.org/10.1371/journal.pone.0136497. Read: the
PLoS PDF.

p. 6-7, "Contact patterns from sensor data":

> During the data collection, 67,613 contact events were registered between the 327
> students carrying wearable sensors, with a cumulative duration of 3,770,160s

> the average duration of a contact was 56 seconds, with however 75% of the contacts
> having duration smaller than 1 minute and on the other hand 2% lasting more than 5
> minutes.

p. 10, Table 2 (sensor network on one day, 295 students): "Avg. Degree 15(8)", "Maximal
Clique 9".

Plain statement: one school day gives about 15 distinct contacts per student. My
arithmetic: about 83 contact events and 77 minutes of contact per student per day.

### 1f. Group sizes: Cencetti et al. 2021 (maximal cliques per 20-s window)

G. Cencetti, F. Battiston, B. Lepri, M. Karsai, "Temporal properties of higher-order
interactions in social networks", Scientific Reports 11:7028 (2021).
https://doi.org/10.1038/s41598-021-86469-8. Read: Europe PMC full text, PMC8007734.

Results, "Temporal higher-order social interactions":

> if at a time t there are n∗(n+1)/2 dyads between the members of a set of n nodes such
> that they form a fully connected clique, we promote the n∗(n+1)/2 links to a
> n-hyperedge.

(The formula is printed this way in the paper; n(n-1)/2 is the number of pairs.)

Results, "Statistics of higher-order interactions":

> Smaller interactions involving less people are more numerous in all datasets, however
> different settings are characterized by different statistics: for instance, among the
> Sociopatterns datasets, the conference reveals the presence of very large
> aggregations, with up to events of size 9, while in the hospital and workplace
> settings the group sizes are limited to 5 and 4 respectively.

> these interactions are mainly pairwise [...] interactions of size 4 are poorly
> represented (less than 20 in 11 days). In addition, the workplace network has the
> highest ratio (nearly one and half orders of magnitude) between the number of dyadic
> and triplet interactions.

Plain statement: in sensor data, groups seen as full cliques in one 20-s window are
mostly pairs; at the workplace there are roughly 30 pairs for every triple and almost no
groups of 4; at the conference cliques reach size 9. The exact counts per size are only
in Fig. 2b (a histogram), which I did not read off. This is the same clique method our
spec uses for the sensor hypergraph, so these sizes are what sensors show, not true
group sizes (see Part 2).

Also relevant, Cattuto et al. 2010 (entry 2a below), p. 4, Fig. 2 caption: "The data
correspond to respectively 8700, 17000 and 600000 contact events registered at the ISI,
SFHH and 25C3 deployments" and "The number of triangles registered are 89, 1700 and
600000". At SFHH this is one triangle per 10 pair contacts.

### Summary for Part 1

No source gives the number of gatherings a person attends per day. Closest proxies:

- Distinct contacts per person per day: about 20 to 30 at conferences (HT09, SFHH),
  about 3 to 6 in workplaces (InVS13, InVS15), about 15 in a high school.
- Contact events per person per day (sensor events, mostly under one minute): about 67
  to 83 (my arithmetic, HT09, SFHH, high school).
- Fraction of time in detected contact: about 1.3% in an office; about 10% at a
  conference (my arithmetic from SFHH).
- Groups: mostly pairs. At a workplace, maximal 3-cliques are about 30 times rarer than
  pairs (Cencetti 2021). At a conference, triangles are about 10 times rarer than pair
  contacts (Cattuto 2010, SFHH).

Note that "a contact" in these data is a sensor contact, which is often under a minute
and does not equal a 15-minute gathering. For our simulation, a target of 3 to 10
distinct partners per day (workplace) up to 20 to 30 (conference style) is the range the
data support.


## Part 2. How reliably sensors detect a pair that is together

### 2a. Cattuto et al. 2010 (design specification, not a field test)

C. Cattuto, W. Van den Broeck, A. Barrat, V. Colizza, J.-F. Pinton, A. Vespignani,
"Dynamics of person-to-person interactions from distributed RFID sensor networks", PLoS
ONE 5(7):e11596 (2010). https://doi.org/10.1371/journal.pone.0011596. Read: the PLoS
PDF.

p. 8, Materials and Methods:

> The rate at which low-power packets are emitted and the fraction of time the devices
> spend listening on the contact channel are tuned so that the face-to-face proximity of
> two individuals wearing the RFID tags can be assessed with a probability in excess of
> 99% over an interval of 20 seconds.

p. 8:

> The same is true is the individuals are nearby but are not facing each other.

(That is, no packets are exchanged if two people are close but not facing.)

p. 6:

> The line of sight between two devices that can exchange radio packets lies in a solid
> angle that is narrow enough to generate very few false positives in crowded
> situations.

Plain statement: when two people face each other within about 1.5 m, the badges detect
them in a given 20-s window with probability above 99%. This is the design value. It
says nothing about pairs in the same group who are not facing each other. Génois et al.
2015 (p. 3), Isella et al. 2011 (p. 2), Mastrandrea et al. 2015 (p. 4) and Stehlé et al.
2011 repeat this 99% figure and cite Cattuto et al.; none of them measures it in the
field.

### 2b. Elmer et al. 2019 (field test against video, the closest direct value)

T. Elmer, K. Chaitanya, P. Purwar, C. Stadtfeld, "The validity of RFID badges measuring
face-to-face interactions", Behavior Research Methods 51:2120-2138 (2019).
https://doi.org/10.3758/s13428-018-1180-y. Read: Europe PMC full text, PMC6797650
(published version). Note: they used OpenBeacon badges and firmware, the same hardware
family as SocioPatterns but not the SocioPatterns firmware, and they scored every
second, not 20-s windows.

Methods Study 1, "Design": 11 people at an after-work get-together, 76.7 minutes of
video.

Methods Study 1, "Human-coded interactions":

> In group conversations, every group member was coded as interacting with every other
> member, irrespective of the role in the group (i.e., speaker or listener).

Results Study 1, "Initial validity":

> Based on the classification results of Table 2, the sensitivity is 49.7%, the
> specificity at 97.0%, and the accuracy at 87.5%, indicating that around 50% of the
> seconds of interactions were detected by the RFID badges and 97% of the seconds of
> non-interactions were correctly identified as such.

Table 2 (seconds, video vs RFID): video positive and RFID positive 25,326; video
positive and RFID negative 25,674; video negative and RFID positive 6,086; video
negative and RFID negative 196,025.

Results Study 1, "The contribution of a single data processing strategy":

> Merging interactions that are maximally 75 s apart showed the best fit, with an
> accuracy of 88.9% (shown), and a sensitivity and specificity of 65.6% and 94.7%,
> respectively

Results Study 1, "Description of the data":

> the video-coded data records more interaction time (14.3 h, 20.3% of the possible 70.3
> h of dyadic data) than the RFID badges (8.4 h, 12.0%).

Discussion Study 1:

> Surprisingly, however, the strategy to close triads did not increase the validity.
> This indicates that measurements tend not to be much worse in the case of group
> interactions.

Plain statement: when the truth is "these people are in the same conversation group",
the badges detect a given pair in a given second about 50% of the time (about 66% after
filling gaps shorter than 75 s). This is the best match to our d, since the video coding
counts every pair in a group as together, as our simulation does. It is per second, not
per 20-s window, so the per-window value is likely higher, but the paper does not report
it.

### 2c. Smieszek et al. 2016 (conference, SocioPatterns badges vs diaries)

T. Smieszek, S. Castell, A. Barrat, C. Cattuto, P. J. White, G. Krause, "Contact diaries
versus wearable proximity sensors in measuring contact patterns at a conference: method
comparison and participants' attitudes", BMC Infectious Diseases 16:341 (2016).
https://doi.org/10.1186/s12879-016-1676-y. Read: Europe PMC full text, PMC4957345.

Methods, "Wearable sensors":

> We used active Radio Frequency Identification (RFID) sensors developed by the
> SocioPatterns collaboration

> it is possible that situations occur where two individuals are in close proximity but
> do not face each other, e.g., sitting next to each other in a lecture hall, resulting
> potentially in no registered contact event by the sensors

Results, "Differences between sensor and diary data":

> If using the reported contacts as denominator, and calculating the proportion of all
> reported contacts that were also detected by the sensor network, we estimated a
> detection probability 57.5 % [45.5-68.8 %] in the <5 min duration category; 60.3 %
> [46.0-75.0 %] in the 5-15 min category; 66.1 % [51.4-82.0 %] in the 15-60 min
> category; 95.2 % [87.0-100 %] in the >60 min category.

Discussion, "Under- and overrecording with sensors" lists causes: receivers did not
cover the canteen or outdoor spaces, and "participants [...] place their sensor under a
jacket or at another inappropriate place". It adds:

> These reasons as well as reporting of angled or distant conversations might explain
> why about 42 % of short contacts (less than 5 min) that were reported were not
> recorded by the sensors.

Plain statement: of pairs who said they talked for 5 to 60 minutes in total that day,
the sensors recorded any contact at all for only about 60 to 66%; for pairs together
over an hour, 95%. This is a whole-day, per-pair value, not per 20-s window.

### 2d. Mastrandrea et al. 2015 (high school, SocioPatterns badges vs diaries)

Same reference as 1e. p. 10:

> Overall, 70.4% of the links obtained from contact diaries correspond to contacts
> registered by the sensors, while only 41.4% of the contacts registered by the sensors
> find a match in the contact diary.

p. 12, Table 4 (rows: diary category; first column: "Not detected" by sensors; last
column: row total). Row "15-60 min": not detected "17 (29%)", total "59 (100%)". Row
for more than 60 minutes: not detected "27 (21%)", total "128 (100%)".

p. 10, Table 2 caption:

> On the day of collection of the contact diaries, only 295 students out of the 327
> participating correctly wore their sensors.

Plain statement: about 30% of contacts students reported were never seen by the sensors
that day, including 29% of pairs reporting 15 to 60 minutes together and 21% reporting
over an hour. Some of these may be diary errors or contacts outside the covered area, so
this is an upper bound on the sensor miss rate.

### Summary for Part 2

There is no published field value for "probability that a pair in the same group is
detected in a given 20-s window", and no source reports how often a group of k people
appears as a full k-clique in sensor data. The closest values:

- Design value, two people facing each other: above 99% per 20-s window (Cattuto 2010).
- Field value against video, all pairs in the same conversation group: about 50% per
  second, 66% after filling gaps under 75 s (Elmer 2019).
- Whole-day value, pairs who report 5 to 60 minutes together: about 60 to 71% are ever
  detected (Smieszek 2016, conference; Mastrandrea 2015, high school).

What this means for our d: the whole-day numbers cannot come from independent misses per
20-s window. A 15-minute gathering has 45 windows, so with any d above 0.1 a pair would
almost surely be seen at least once (my arithmetic: 1 - 0.9^45 is about 0.99). The 30 to
40% of pairs never seen means some pairs in a group are missed for the whole gathering
(not facing, badge covered, outside reader range). One way to match both facts: each
pair in a gathering is "visible" with probability about 0.6 to 0.7, and a visible pair
is detected in each 20-s window with probability about 0.5 to 0.66.

For cliques, my arithmetic only (not from any source): if each of the k(k-1)/2 pairs in
a group were detected independently with probability p in a window, a full clique of k
would appear with probability p^(k(k-1)/2). With p = 0.66 this is 0.29 for k = 3, 0.08
for k = 4, 0.02 for k = 5 and 0.002 for k = 6. This would explain why sensor data show
mostly pairs (Cencetti 2021) even when people stand in larger groups, but no source
tests this directly.
