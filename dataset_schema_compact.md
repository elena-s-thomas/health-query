# FHIR Synthea Dataset Schema (Compact)

**Dataset:** `bigquery-public-data.fhir_synthea`
**Tables:** 17

## Common FHIR Types

All tables include these common fields: id, meta, identifier[], implicitRules, language, text

### Key Type Definitions
- **Reference**: Links to other resources (with display, identifier, reference fields)
- **CodeableConcept**: Coded value with text (coding[], text)
- **Period**: Time range (start, end)
- **Identifier**: Resource identifier (system, value, type, use)
- **Annotation**: Note with metadata (author, time, text)

## Tables

### allergy_intolerance
- **Rows:** 551,781
- **Size:** 0.16 GB
- **Key Fields:**
  **References:**
  - patient (Reference<Patient>)
  **Codes:**
  - code (CodeableConcept)
  **Attributes:**
  - lastOccurrence
  - assertedDate
  - category
  - clinicalStatus
  - criticality
  **Other:**
  - asserter (RECORD)
  - note (Annotation[])
  - onset (RECORD)
  - reaction (RECORD)
  - recorder (RECORD)

### basic
- **Rows:** 1,176,837
- **Size:** 0.23 GB
- **Key Fields:**
  **References:**
  - subject (Reference<Patient/Group>)
  **Codes:**
  - code (CodeableConcept)
  **Attributes:**
  - created
  **Other:**
  - author (RECORD)

### care_plan
- **Rows:** 3,286,012
- **Size:** 1.66 GB
- **Key Fields:**
  **References:**
  - basedOn (Reference)
  - context (Reference<Encounter>)
  **Codes:**
  - category (CodeableConcept)
  **Attributes:**
  - description
  - title
  **Other:**
  - author (RECORD)
  - careTeam (RECORD)
  - definition (RECORD)
  - note (Annotation[])
  - partOf (RECORD)
  - replaces (RECORD)
  - supportingInfo (RECORD)
  - activity (RECORD)
  - addresses (RECORD)
  - goal (RECORD)

### claim
- **Rows:** 51,914,513
- **Size:** 21.24 GB
- **Key Fields:**
  **Attributes:**
  - created
  **Other:**
  - accident (RECORD)
  - careTeam (RECORD)
  - employmentImpacted (RECORD)
  - enterer (RECORD)
  - facility (RECORD)
  - fundsReserve (RECORD)
  - hospitalization (RECORD)
  - insurance (RECORD)
  - insurer (RECORD)
  - originalPrescription (RECORD)
  - payee (RECORD)
  - priority (RECORD)
  - provider (RECORD)
  - referral (RECORD)

### condition
- **Rows:** 8,839,008
- **Size:** 3.8 GB
- **Key Fields:**
  **References:**
  - context (Reference<Encounter>)
  - subject (Reference<Patient/Group>)
  **Codes:**
  - category (CodeableConcept)
  - code (CodeableConcept)
  **Attributes:**
  - assertedDate
  - clinicalStatus
  - verificationStatus
  **Other:**
  - asserter (RECORD)
  - bodySite (RECORD)
  - evidence (RECORD)
  - note (Annotation[])
  - severity (RECORD)
  - stage (RECORD)
  - abatement (RECORD)
  - onset (RECORD)

### diagnostic_report
- **Rows:** 14,730,390
- **Size:** 11.3 GB
- **Key Fields:**
  **References:**
  - basedOn (Reference)
  - context (Reference<Encounter>)
  **Codes:**
  - category (CodeableConcept)
  - code (CodeableConcept)
  **Attributes:**
  - conclusion
  - status
  **Other:**
  - codedDiagnosis (RECORD)
  - image (RECORD)
  - imagingStudy (RECORD)
  - performer (RECORD)
  - presentedForm (RECORD)
  - specimen (RECORD)
  - effective (RECORD)
  - issued (TIMESTAMP)
  - result (RECORD)

### encounter
- **Rows:** 40,327,902
- **Size:** 18.21 GB
- **Key Fields:**
  **References:**
  - location (Reference<Location>)
  **Other:**
  - account (RECORD)
  - appointment (RECORD)
  - classHistory (RECORD)
  - diagnosis (RECORD)
  - episodeOfCare (RECORD)
  - incomingReferral (RECORD)
  - length (RECORD)
  - partOf (RECORD)
  - priority (RECORD)
  - statusHistory (RECORD)
  - shr_action_PerformedContext_extension (RECORD)
  - class (RECORD)
  - hospitalization (RECORD)
  - participant (RECORD)

### explanation_of_benefit
- **Rows:** 40,332,402
- **Size:** 126.76 GB
- **Key Fields:**
  **Attributes:**
  - disposition
  **Other:**
  - accident (RECORD)
  - addItem (RECORD)
  - benefitBalance (RECORD)
  - claimResponse (RECORD)
  - employmentImpacted (RECORD)
  - enterer (RECORD)
  - facility (RECORD)
  - form (RECORD)
  - hospitalization (RECORD)
  - information (RECORD)
  - insurer (RECORD)
  - originalPrescription (RECORD)
  - outcome (RECORD)
  - payee (RECORD)

### goal
- **Rows:** 2,116,295
- **Size:** 0.24 GB
- **Key Fields:**
  **References:**
  - outcomeReference (Reference)
  - subject (Reference<Patient/Group>)
  **Codes:**
  - category (CodeableConcept)
  **Attributes:**
  - statusDate
  - statusReason
  - status
  **Other:**
  - addresses (RECORD)
  - expressedBy (RECORD)
  - note (Annotation[])
  - outcomeCode (RECORD)
  - priority (RECORD)
  - start (RECORD)
  - target (RECORD)
  - description (RECORD)

### imaging_study
- **Rows:** 829,305
- **Size:** 0.43 GB
- **Key Fields:**
  **References:**
  - basedOn (Reference)
  - procedureReference (Reference)
  - context (Reference<Encounter>)
  - patient (Reference<Patient>)
  **Attributes:**
  - availability
  - description
  **Other:**
  - accession (RECORD)
  - endpoint (RECORD)
  - interpreter (RECORD)
  - modalityList (RECORD)
  - procedureCode (RECORD)
  - reason (RECORD)
  - referrer (RECORD)
  - numberOfInstances (INTEGER)
  - numberOfSeries (INTEGER)

### immunization
- **Rows:** 14,641,905
- **Size:** 5.03 GB
- **Key Fields:**
  **References:**
  - location (Reference<Location>)
  - practitioner (Reference<Practitioner>)
  **Attributes:**
  - expirationDate
  - lotNumber
  - date
  **Other:**
  - doseQuantity (RECORD)
  - explanation (RECORD)
  - manufacturer (RECORD)
  - note (Annotation[])
  - reaction (RECORD)
  - reportOrigin (RECORD)
  - route (RECORD)
  - site (RECORD)
  - vaccinationProtocol (RECORD)
  - shr_action_PerformedContext_extension (RECORD)

### medication_request
- **Rows:** 11,589,611
- **Size:** 6.69 GB
- **Key Fields:**
  **References:**
  - basedOn (Reference)
  **Codes:**
  - category (CodeableConcept)
  **Attributes:**
  - priority
  **Other:**
  - definition (RECORD)
  - detectedIssue (RECORD)
  - dispenseRequest (RECORD)
  - eventHistory (RECORD)
  - groupIdentifier (RECORD)
  - note (Annotation[])
  - priorPrescription (RECORD)
  - reasonCode (RECORD)
  - recorder (RECORD)
  - substitution (RECORD)
  - supportingInformation (RECORD)
  - shr_action_RequestedContext_extension (RECORD)

### observation
- **Rows:** 209,771,821
- **Size:** 96.37 GB
- **Key Fields:**
  **References:**
  - basedOn (Reference)
  - referenceRange (Reference)
  - context (Reference<Encounter>)
  **Codes:**
  - category (CodeableConcept)
  - code (CodeableConcept)
  **Attributes:**
  - comment
  **Other:**
  - bodySite (RECORD)
  - dataAbsentReason (RECORD)
  - device (RECORD)
  - interpretation (RECORD)
  - method (RECORD)
  - performer (RECORD)
  - related (RECORD)
  - specimen (RECORD)
  - component (RECORD)

### organization
- **Rows:** 129
- **Size:** 0.0 GB
- **Key Fields:**
  **Attributes:**
  - alias
  - name
  **Other:**
  - active (BOOLEAN)
  - endpoint (RECORD)
  - partOf (RECORD)
  - address (RECORD)
  - contact (RECORD)
  - telecom (RECORD)
  - type (RECORD)

### patient
- **Rows:** 1,176,837
- **Size:** 1.63 GB
- **Key Fields:**
  **Other:**
  - active (BOOLEAN)
  - animal (RECORD)
  - contact (RECORD)
  - generalPractitioner (RECORD)
  - link (RECORD)
  - managingOrganization (RECORD)
  - photo (RECORD)
  - birthPlace (RECORD)
  - disability_adjusted_life_years (RECORD)
  - patient_mothersMaidenName (RECORD)
  - quality_adjusted_life_years (RECORD)
  - shr_actor_FictionalPerson_extension (RECORD)
  - shr_demographics_SocialSecurityNumber_extension (RECORD)
  - shr_entity_FathersName_extension (RECORD)
  - shr_entity_Person_extension (RECORD)

### practitioner
- **Rows:** 129
- **Size:** 0.0 GB
- **Key Fields:**
  **Attributes:**
  - birthDate
  - gender
  **Other:**
  - communication (RECORD)
  - photo (RECORD)
  - qualification (RECORD)
  - telecom (RECORD)
  - active (BOOLEAN)
  - address (RECORD)
  - name (RECORD)

### procedure
- **Rows:** 32,660,192
- **Size:** 13.66 GB
- **Key Fields:**
  **References:**
  - basedOn (Reference)
  - location (Reference<Location>)
  **Codes:**
  - code (CodeableConcept)
  - category (CodeableConcept)
  **Other:**
  - bodySite (RECORD)
  - complication (RECORD)
  - complicationDetail (RECORD)
  - definition (RECORD)
  - focalDevice (RECORD)
  - followUp (RECORD)
  - notDone (BOOLEAN)
  - notDoneReason (RECORD)
  - note (Annotation[])
  - outcome (RECORD)
  - partOf (RECORD)
  - performer (RECORD)

