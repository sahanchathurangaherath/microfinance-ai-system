import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const createClientSchema = z.object({
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  nic_number: z.string().min(5, "NIC number is required"),
  date_of_birth: z.string().min(1, "Date of birth is required"),
  gender: z.enum(["M", "F", "O"]),
  phone_primary: z.string().min(9, "Valid phone number is required"),
  phone_secondary: z.string().optional(),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  preferred_language: z.enum(["en", "si", "ta"]),
});

export type CreateClientFormData = z.infer<typeof createClientSchema>;

export const clientAddressSchema = z.object({
  address_type: z.string().min(1, "Address type is required"),
  address_line_1: z.string().min(1, "Address is required"),
  address_line_2: z.string().optional(),
  city: z.string().min(1, "City is required"),
  district: z.string().min(1, "District is required"),
  province: z.string().min(1, "Province is required"),
  is_primary: z.boolean().optional(),
});

export type ClientAddressFormData = z.infer<typeof clientAddressSchema>;

export const clientBusinessSchema = z.object({
  business_name: z.string().min(1, "Business name is required"),
  business_type: z.string().min(1, "Business type is required"),
  business_description: z.string().optional(),
  years_in_operation: z.number().min(0),
  number_of_employees: z.number().min(0),
  business_address: z.string().optional(),
  monthly_revenue: z.number().min(0).optional(),
});

export type ClientBusinessFormData = z.infer<typeof clientBusinessSchema>;

export const clientIncomeSchema = z.object({
  income_source: z.string().min(1, "Income source is required"),
  monthly_income: z.number().min(0, "Monthly income is required"),
  other_income: z.number().min(0),
  monthly_expenses: z.number().min(0),
  existing_debt_monthly: z.number().min(0),
  number_of_dependents: z.number().min(0),
});

export type ClientIncomeFormData = z.infer<typeof clientIncomeSchema>;

export const loanApplicationSchema = z.object({
  client: z.number({ message: "Client is required" }),
  loan_product: z.number().optional(),
  requested_amount: z.number().min(1, "Amount must be greater than 0"),
  requested_duration_months: z
    .number()
    .min(1, "Duration must be at least 1 month")
    .max(120, "Duration cannot exceed 120 months"),
  loan_purpose: z.enum([
    "BUSINESS_EXPANSION", "WORKING_CAPITAL", "EQUIPMENT_PURCHASE",
    "AGRICULTURE", "EDUCATION", "MEDICAL", "HOME_IMPROVEMENT",
    "DEBT_CONSOLIDATION", "OTHER",
  ]),
  purpose_description: z.string().optional(),
  officer_notes: z.string().optional(),
});

export type LoanApplicationFormData = z.infer<typeof loanApplicationSchema>;

export const cashflowSchema = z.object({
  monthly_income: z.number().min(0),
  other_income: z.number().min(0),
  monthly_expenses: z.number().min(0),
  existing_loan_payments: z.number().min(0),
  proposed_monthly_payment: z.number().min(0),
  officer_assessment_notes: z.string().optional(),
});

export type CashflowFormData = z.infer<typeof cashflowSchema>;

export const createUserSchema = z
  .object({
    username: z.string().min(3, "Username must be at least 3 characters"),
    email: z.string().email("Invalid email"),
    first_name: z.string().min(1, "First name is required"),
    last_name: z.string().min(1, "Last name is required"),
    role: z.enum([
      "admin", "loan_officer", "risk_analyst", "branch_manager",
      "credit_committee", "collections_officer", "compliance_officer", "finance_staff",
    ]),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
    phone: z.string().optional(),
    branch: z.string().optional(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type CreateUserFormData = z.infer<typeof createUserSchema>;

export const changePasswordSchema = z
  .object({
    old_password: z.string().min(1, "Current password is required"),
    new_password: z.string().min(8, "New password must be at least 8 characters"),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email address"),
});

export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    new_password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export const approvalDecisionSchema = z.object({
  decision: z.enum(["APPROVED", "REJECTED", "MORE_INFO", "ESCALATE"]),
  comments: z.string().min(1, "Comments are required"),
  override_reason: z.string().optional(),
});

export type ApprovalDecisionFormData = z.infer<typeof approvalDecisionSchema>;
