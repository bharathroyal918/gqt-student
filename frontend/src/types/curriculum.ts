export interface CurriculumTopic {
  orderIndex: number;
  title: string;
  slug: string;
  description: string;
}

export interface StudentModuleProgress {
  moduleId: string;
  orderIndex: number;
  title: string;
  isUnlocked: boolean;
  isCompleted: boolean;
  passingPercentage: number;
  questionsTotal: number;
  questionsSolved: number;
}
