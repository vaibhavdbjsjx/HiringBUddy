import emailjs from '@emailjs/browser';
import type { Candidate } from './api';

// EmailJS Configuration
const EMAILJS_SERVICE_ID = 'service_qziw7ss';
const EMAILJS_PUBLIC_KEY = 'tv6pvzB9ipsXUNT3g';
const INTERVIEW_TEMPLATE_ID = 'template_tcmhs71';
const STATUS_TEMPLATE_ID = 'template_mhjmw5z';

export const sendInterviewEmail = async (candidate: Candidate, interviewLink: string) => {
  try {
    console.log('Initiating EmailJS delivery for Interview Invite to:', candidate.email);
    
    const templateParams = {
      to_email: candidate.email,
      candidate_name: candidate.name,
      job_role: 'Software Engineer', // Default role if not available
      interview_link: interviewLink,
      hr_email: 'hr@hiringbuddy.ai'
    };

    const response = await emailjs.send(
      EMAILJS_SERVICE_ID,
      INTERVIEW_TEMPLATE_ID,
      templateParams,
      EMAILJS_PUBLIC_KEY
    );

    console.log('Interview email successfully sent!', response.status, response.text);
    return true;
  } catch (error) {
    console.error('Failed to send interview email:', error);
    return false; 
  }
};

export const sendStatusEmail = async (candidate: Candidate, type: 'shortlist' | 'reject') => {
  try {
    console.log(`Initiating EmailJS delivery for ${type} to:`, candidate.email);

    const isShortlist = type === 'shortlist';
    
    const templateParams = {
      to_email: candidate.email,
      to_name: candidate.name,
      candidate_name: candidate.name,
      title: isShortlist ? 'Congratulations! You are Shortlisted 🎉' : 'Update on your Application',
      title_color: isShortlist ? '#4ade80' : '#f87171',
      border_color: isShortlist ? '#22c55e' : '#ef4444',
      button_color: isShortlist ? '#16a34a' : '#dc2626',
      application_status: isShortlist ? 'Shortlisted' : 'Not Selected',
      badge_text: isShortlist ? 'Next Stage' : 'Closed',
      status_message: isShortlist 
        ? `Hi ${candidate.name}, we are thrilled to inform you that your profile has been shortlisted for the next round of interviews. Our HR team will contact you shortly to schedule your technical round.`
        : `Hi ${candidate.name}, thank you for your time and interest. Unfortunately, we have decided to move forward with other candidates who more closely match our requirements at this time. We will keep your resume on file for future opportunities.`,
      footer_message: 'HiringBuddy AI Recruitment Team'
    };

    const response = await emailjs.send(
      EMAILJS_SERVICE_ID,
      STATUS_TEMPLATE_ID,
      templateParams,
      EMAILJS_PUBLIC_KEY
    );

    console.log('Status email successfully sent!', response.status, response.text);
    return true;
  } catch (error) {
    console.error('Failed to send status email:', error);
    return false;
  }
};
