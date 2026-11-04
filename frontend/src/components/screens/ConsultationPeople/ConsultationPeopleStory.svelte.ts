import ConsultationPeople from "./ConsultationPeople.svelte";
import {
  COLLEAGUE,
  CONSULTATION_ID,
  CREATOR,
  YOU,
  userAssignmentMock,
  consultationErrorMock,
  invitedConsultationMock,
  manyPeopleConsultationMock,
  ownedConsultationMock,
  userRemovalMock,
  staffUserMock,
  userMock,
} from "./mocks";

const consultationId = $state(CONSULTATION_ID);
const ownerMocks = [
  ownedConsultationMock,
  userMock,
  userAssignmentMock,
  userRemovalMock(COLLEAGUE.id),
  userRemovalMock(CREATOR.id),
];

export default {
  name: "ConsultationPeople",
  component: ConsultationPeople,
  category: "Screens",
  props: [{ name: "consultationId", value: consultationId, type: "text" }],
  mocks: ownerMocks,
  stories: [
    {
      name: "Owner",
      mocks: ownerMocks,
      props: {
        consultationId: CONSULTATION_ID,
        backHref: `/consultations/${CONSULTATION_ID}`,
        backText: "Back to the consultation",
      },
    },
    {
      name: "Invited",
      mocks: [invitedConsultationMock, userMock],
      props: {
        consultationId: CONSULTATION_ID,
        backHref: `/consultations/${CONSULTATION_ID}`,
        backText: "Back to the consultation",
      },
    },
    {
      name: "Staff on another person's consultation",
      mocks: [
        invitedConsultationMock,
        staffUserMock,
        userAssignmentMock,
        userRemovalMock(COLLEAGUE.id),
        userRemovalMock(YOU.id),
      ],
      props: {
        consultationId: CONSULTATION_ID,
        backHref: `/consultations/${CONSULTATION_ID}`,
        backText: "Back to the consultation",
      },
    },
    {
      name: "More than ten people",
      mocks: [manyPeopleConsultationMock, userMock],
      props: {
        consultationId: CONSULTATION_ID,
        backHref: `/consultations/${CONSULTATION_ID}`,
        backText: "Back to the consultation",
      },
    },
    {
      name: "Fetch Error",
      mocks: [consultationErrorMock, userMock],
      props: {
        consultationId: CONSULTATION_ID,
        backHref: `/consultations/${CONSULTATION_ID}`,
        backText: "Back to the consultation",
      },
    },
  ],
};
