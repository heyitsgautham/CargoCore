<template>
  <Background image-url="https://images.unsplash.com/photo-1622224408917-9dfb43de2cd4?crop=entropy&cs=tinysrgb&fit=max&fm=jpg">
    <Navbar />
    <AIHelpOrb />

    <div class="min-h-screen flex items-center justify-center px-8 pt-32 pb-20">
      <div
        v-motion
        :initial="{ opacity: 0, scale: 0.95 }"
        :enter="{ opacity: 1, scale: 1, transition: { duration: 500 } }"
        class="w-full max-w-2xl"
      >
        <GlassCard class-name="p-8" :animate="false">
          <!-- Logo -->
          <div class="flex justify-center mb-6">
            <img
              v-motion
              :initial="{ scale: 0.8, opacity: 0 }"
              :enter="{ scale: 1, opacity: 1, transition: { delay: 200, type: 'spring', stiffness: 200 } }"
              src="/a-standalone-vector-logo-icon-based-exac_VyOETc4yR5-IePoBy-7pGw_etxGKfs2SfKMsgaJ3OD4CQ_sd.jpeg"
              alt="Cargo Core Logo"
              class="h-16 w-auto"
            />
          </div>

          <!-- Header -->
          <div
            v-motion
            :initial="{ opacity: 0, y: 10 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 300 } }"
            class="text-center mb-8"
          >
            <h2 class="text-2xl font-bold text-white mb-2">
              Create Your Account
            </h2>
            <p class="text-white/60 text-sm">
              Join Cargo Core as a Customer or Vendor
            </p>
          </div>

          <!-- Progress Steps -->
          <div class="mb-8">
            <div class="flex items-center justify-between mb-2">
              <div v-for="(step, index) in filteredSteps" :key="step.id" class="flex-1">
                <div class="flex items-center">
                  <div
                    :class="[
                      'w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300',
                      currentStep > step.id
                        ? 'bg-[#00C4FF] text-white'
                        : currentStep === step.id
                        ? 'bg-gradient-to-r from-[#00C4FF] to-[#FF9500] text-white'
                        : 'bg-white/10 text-white/50',
                    ]"
                  >
                    <CheckCircle2 v-if="currentStep > step.id" class="w-5 h-5" />
                    <span v-else>{{ step.displayId }}</span>
                  </div>
                  <div
                    v-if="index < filteredSteps.length - 1"
                    :class="[
                      'flex-1 h-0.5 mx-2 transition-all duration-300',
                      currentStep > step.id ? 'bg-[#00C4FF]' : 'bg-white/10',
                    ]"
                  />
                </div>
                <div class="mt-2 text-center">
                  <p :class="['text-xs font-medium', currentStep >= step.id ? 'text-white' : 'text-white/50']">
                    {{ step.title }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Form Steps -->
          <Transition name="slide" mode="out-in">
            <!-- Step 1: Role Selection -->
            <div v-if="currentStep === 1" key="step1" class="space-y-6">
              <div class="text-center mb-4">
                <h3 class="text-lg font-semibold text-white mb-2">Choose Your Role</h3>
                <p class="text-white/60 text-sm">Select how you'll use Cargo Core</p>
              </div>
              
              <div class="grid grid-cols-2 gap-4">
                <!-- Customer Card -->
                <button
                  type="button"
                  @click="formData.role = 'customer'"
                  :class="[
                    'p-6 rounded-xl border-2 transition-all duration-300 text-left',
                    formData.role === 'customer'
                      ? 'bg-[#00C4FF]/20 border-[#00C4FF]'
                      : 'bg-white/5 border-white/10 hover:border-[#00C4FF50]'
                  ]"
                >
                  <div class="mb-4">
                    <div :class="[
                      'w-12 h-12 rounded-lg flex items-center justify-center mb-3',
                      formData.role === 'customer' ? 'bg-[#00C4FF]/30' : 'bg-white/10'
                    ]">
                      <Users class="w-6 h-6 text-[#00C4FF]" />
                    </div>
                    <h4 class="text-white font-semibold text-lg mb-2">Customer</h4>
                    <p class="text-white/60 text-sm">
                      Book logistics services and track shipments
                    </p>
                  </div>
                  <div v-if="formData.role === 'customer'" class="flex items-center gap-2 text-[#00C4FF] text-sm font-medium">
                    <CheckCircle2 class="w-4 h-4" />
                    <span>Selected</span>
                  </div>
                </button>

                <!-- Vendor Card -->
                <button
                  type="button"
                  @click="formData.role = 'vendor'"
                  :class="[
                    'p-6 rounded-xl border-2 transition-all duration-300 text-left',
                    formData.role === 'vendor'
                      ? 'bg-[#8B5CF6]/20 border-[#8B5CF6]'
                      : 'bg-white/5 border-white/10 hover:border-[#8B5CF6]/50'
                  ]"
                >
                  <div class="mb-4">
                    <div :class="[
                      'w-12 h-12 rounded-lg flex items-center justify-center mb-3',
                      formData.role === 'vendor' ? 'bg-[#8B5CF6]/30' : 'bg-white/10'
                    ]">
                      <Users class="w-6 h-6 text-[#A78BFA]" />
                    </div>
                    <h4 class="text-white font-semibold text-lg mb-2">Vendor</h4>
                    <p class="text-white/60 text-sm">
                      Offer logistics services and manage fleet
                    </p>
                  </div>
                  <div v-if="formData.role === 'vendor'" class="flex items-center gap-2 text-[#8B5CF6] text-sm font-medium">
                    <CheckCircle2 class="w-4 h-4" />
                    <span>Selected</span>
                  </div>
                </button>
              </div>
            </div>

            <!-- Step 2: Basic Info -->
            <div v-else-if="currentStep === 2" key="step2" class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <GlassInput
                  v-model="formData.firstName"
                  type="text"
                  placeholder="First Name"
                  :icon="User"
                  required
                />
                <GlassInput
                  v-model="formData.lastName"
                  type="text"
                  placeholder="Last Name"
                  :icon="User"
                  required
                />
              </div>

              <GlassInput
                v-model="formData.email"
                type="email"
                placeholder="Email Address"
                :icon="Mail"
                required
              />

              <GlassInput
                v-model="formData.phone"
                type="tel"
                placeholder="Phone Number"
                :icon="Phone"
                required
              />

              <div class="relative">
                <GlassInput
                  v-model="formData.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Password"
                  :icon="Lock"
                  required
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-4 top-1/2 -translate-y-1/2 text-white/50 hover:text-[#00C4FF] transition-colors duration-300"
                >
                  <EyeOff v-if="showPassword" class="w-5 h-5" />
                  <Eye v-else class="w-5 h-5" />
                </button>
              </div>

              <div class="relative">
                <GlassInput
                  v-model="formData.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="Confirm Password"
                  :icon="Lock"
                  required
                />
                <button
                  type="button"
                  @click="showConfirmPassword = !showConfirmPassword"
                  class="absolute right-4 top-1/2 -translate-y-1/2 text-white/50 hover:text-[#00C4FF] transition-colors duration-300"
                >
                  <EyeOff v-if="showConfirmPassword" class="w-5 h-5" />
                  <Eye v-else class="w-5 h-5" />
                </button>
              </div>
            </div>

            <!-- Step 3: Business Details -->
            <div v-else-if="currentStep === 3" key="step3" class="space-y-4">
              <!-- For VENDORS: Full business details -->
              <template v-if="formData.role === 'vendor'">
                <GlassInput
                  v-model="formData.companyName"
                  type="text"
                  placeholder="Company Name"
                  :icon="Building2"
                  required
                />

                <div>
                  <label class="block text-white/70 text-sm mb-3">Services You Offer</label>
                  <div class="grid grid-cols-2 gap-3">
                    <button
                      v-for="service in serviceOptions"
                      :key="service"
                      type="button"
                      @click="toggleService(service)"
                      :class="[
                        'px-4 py-3 rounded-lg text-sm font-medium transition-all duration-300',
                        formData.services.includes(service)
                          ? 'bg-[#00C4FF]/20 border-2 border-[#00C4FF] text-white'
                          : 'bg-white/5 border border-white/10 text-white/70 hover:border-[#00C4FF50]',
                      ]"
                    >
                      {{ service }}
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-white/70 text-sm mb-2">Business Verification Document *</label>
                  <div class="relative">
                    <input
                      type="file"
                      @change="handleFileUpload"
                      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                      class="hidden"
                      id="business-document"
                      required
                    />
                    <label
                      for="business-document"
                      :class="[
                        'flex items-center justify-between w-full px-4 py-3.5 pl-12 bg-white/5 backdrop-blur-xl border rounded-lg cursor-pointer transition-all duration-300',
                        formData.businessDocument
                          ? 'border-[#00C4FF] hover:border-[#00D4FF]'
                          : 'border-white/10 hover:border-[#00C4FF50]'
                      ]"
                    >
                      <span :class="formData.businessDocument ? 'text-white' : 'text-white/50'">
                        {{ formData.businessDocument ? formData.businessDocument.name : 'Upload business license, registration, or tax document' }}
                      </span>
                      <CheckCircle2 v-if="formData.businessDocument" class="w-5 h-5 text-[#00C4FF]" />
                    </label>
                    <div class="absolute left-4 top-1/2 -translate-y-1/2 text-white/50 pointer-events-none">
                      <Building2 class="w-5 h-5" />
                    </div>
                  </div>
                  <p class="text-white/40 text-xs mt-2">Accepted formats: PDF, DOC, DOCX, JPG, PNG (Max 10MB)</p>
                </div>
              </template>

              <!-- For CUSTOMERS: Simple preferences -->
              <template v-else-if="formData.role === 'customer'">
                <GlassInput
                  v-model="formData.companyName"
                  type="text"
                  placeholder="Company Name (Optional)"
                  :icon="Building2"
                />

                <div>
                  <label class="block text-white/70 text-sm mb-3">Services You Need</label>
                  <div class="grid grid-cols-2 gap-3">
                    <button
                      v-for="service in serviceOptions"
                      :key="service"
                      type="button"
                      @click="toggleService(service)"
                      :class="[
                        'px-4 py-3 rounded-lg text-sm font-medium transition-all duration-300',
                        formData.services.includes(service)
                          ? 'bg-[#00C4FF]/20 border-2 border-[#00C4FF] text-white'
                          : 'bg-white/5 border border-white/10 text-white/70 hover:border-[#00C4FF50]',
                      ]"
                    >
                      {{ service }}
                    </button>
                  </div>
                </div>

                <div class="mt-4 p-4 bg-[#00C4FF]/10 rounded-lg border border-[#00C4FF]/30">
                  <p class="text-white/80 text-sm">
                    ℹ️ Select the logistics services you're interested in. You can always update this later.
                  </p>
                </div>
              </template>
            </div>

            <!-- Step 4: Address -->
            <div v-else-if="currentStep === 4" key="step4" class="space-y-4">
              <!-- Detect Location Button -->
              <button
                type="button"
                @click="detectLocation"
                :disabled="isDetectingLocation"
                class="w-full px-4 py-3.5 rounded-lg bg-gradient-to-r from-[#00C4FF]/20 to-[#1E3A8A]/20 border border-[#00C4FF]/40 text-white font-medium hover:from-[#00C4FF]/30 hover:to-[#1E3A8A]/30 transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <MapPin :class="['w-5 h-5', isDetectingLocation && 'animate-pulse']" />
                <span v-if="!isDetectingLocation"> Detect My Location</span>
                <span v-else>Detecting location...</span>
              </button>

              <div class="relative flex items-center">
                <div class="flex-1 border-t border-white/20"></div>
                <span class="px-3 text-white/50 text-sm">or enter manually</span>
                <div class="flex-1 border-t border-white/20"></div>
              </div>

              <GlassInput
                v-model="formData.address"
                type="text"
                placeholder="Street Address"
                :icon="MapPin"
                required
              />

              <div class="grid grid-cols-2 gap-4">
                <GlassInput
                  v-model="formData.city"
                  type="text"
                  placeholder="City"
                  :icon="Building2"
                  required
                />
                <GlassInput
                  v-model="formData.state"
                  type="text"
                  placeholder="State"
                  :icon="MapPin"
                  required
                />
              </div>

              <div class="grid grid-cols-2 gap-4">
                <GlassInput
                  v-model="formData.zipCode"
                  type="text"
                  placeholder="ZIP Code"
                  :icon="Home"
                  required
                />
                <GlassInput
                  v-model="formData.country"
                  type="text"
                  placeholder="Country"
                  :icon="MapPin"
                  required
                />
              </div>

              <div class="mt-6 p-4 bg-[#00C4FF]/10 rounded-lg border border-[#00C4FF]/30">
                <p class="text-white/80 text-sm">
                  ℹ️ We'll verify your address to ensure accurate service delivery in your area.
                </p>
              </div>
            </div>

            <!-- Step 5: 2FA Setup Preview -->
            <div v-else-if="currentStep === 5" key="step5" class="text-center py-8">
              <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-[#00C4FF]/20 to-[#1E3A8A]/20 flex items-center justify-center border border-[#00C4FF]/30">
                <CheckCircle2 class="w-10 h-10 text-[#00C4FF]" />
              </div>
              <h3 class="text-xl font-semibold text-white mb-3">
                Almost There!
              </h3>
              <p class="text-white/70 mb-6">
                We have sent a verification code to your email to complete the signup process.
              </p>
              <div class="p-4 bg-white/5 rounded-lg border border-white/10 text-left">
                <p class="text-white/60 text-sm mb-2">Account Summary:</p>
                <div class="space-y-2">
                  <div class="flex justify-between">
                    <span class="text-white/50 text-sm">Role:</span>
                    <span class="text-white text-sm font-medium capitalize">{{ formData.role }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-white/50 text-sm">Name:</span>
                    <span class="text-white text-sm font-medium">
                      {{ formData.firstName }} {{ formData.lastName }}
                    </span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-white/50 text-sm">Email:</span>
                    <span class="text-white text-sm font-medium">{{ formData.email }}</span>
                  </div>
                  <div v-if="formData.companyName" class="flex justify-between">
                    <span class="text-white/50 text-sm">Company:</span>
                    <span class="text-white text-sm font-medium">{{ formData.companyName }}</span>
                  </div>
                </div>
              </div>
            </div>
          </Transition>

          <!-- Navigation Buttons -->
          <div class="flex gap-4 mt-8">
            <GlassButton
              variant="secondary"
              :icon="ArrowLeft"
              class-name="flex-1"
              @click="handleBack"
            >
              Back
            </GlassButton>
            <GlassButton
              variant="primary"
              :is-loading="isLoading"
              :icon="currentStep === 5 ? CheckCircle2 : ArrowRight"
              class-name="flex-1"
              @click="handleNext"
            >
              {{ currentStep === 5 ? 'Verify Email' : 'Next' }}
            </GlassButton>
          </div>

          <!-- Sign In Link -->
          <div
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 500 } }"
            class="mt-6 text-center"
          >
            <p class="text-white/60 text-sm">
              Already have an account?
              <button
                @click="goToSignIn"
                class="text-[#00C4FF] hover:text-[#00D4FF] font-semibold transition-colors duration-300"
              >
                Sign in
              </button>
            </p>
          </div>
        </GlassCard>
      </div>
    </div>
  </Background>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import {
  User,
  Users,
  Mail,
  Phone,
  Lock,
  Building2,
  MapPin,
  Truck,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Eye,
  EyeOff,
  Home,
} from 'lucide-vue-next';
import Background from '../components/Background.vue';
import Navbar from '../components/Navbar.vue';
import AIHelpOrb from '../components/AIHelpOrb.vue';
import GlassCard from '../components/GlassCard.vue';
import GlassInput from '../components/GlassInput.vue';
import GlassButton from '../components/GlassButton.vue';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../composables/useToast';

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast();

const steps = [
  { id: 1, title: 'Select Role', description: 'Choose account type' },
  { id: 2, title: 'Basic Info', description: 'Personal details' },
  { id: 3, title: 'Business Details', description: 'Company information' },
  { id: 4, title: 'Address', description: 'Location verification' },
  { id: 5, title: '2FA Setup', description: 'Security verification' },
];

// Filter steps based on role - customers skip Business Details
const filteredSteps = computed(() => {
  if (formData.role === 'customer') {
    // Show steps 1, 2, 4, 5 for customers (skip step 3)
    return steps.filter(step => step.id !== 3).map((step, index) => ({
      ...step,
      displayId: index + 1
    }));
  }
  // Show all steps for vendors
  return steps.map((step, index) => ({ ...step, displayId: index + 1 }));
});

const currentStep = ref(1);
const isLoading = ref(false);
const isSignupPrepared = ref(false);
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const isDetectingLocation = ref(false);

const formData = reactive({
  role: '',
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: '',
  companyName: '',
  services: [],
  businessDocument: null,
  address: '',
  city: '',
  state: '',
  zipCode: '',
  country: '',
});

const serviceOptions = [
  'House Shifts',
  'Commercial Shipping',
  'Freight Forwarding',
  'Last-Mile Delivery',
  'Warehousing',
  'Cross-Border Logistics',
];

const toggleService = (service) => {
  const index = formData.services.indexOf(service);
  if (index > -1) {
    formData.services.splice(index, 1);
  } else {
    formData.services.push(service);
  }
};

const goToSignIn = () => {
  if (formData.role === 'customer' || formData.role === 'vendor') {
    router.push(`/login/${formData.role}`);
    return;
  }

  router.push('/login-hub');
};

const handleFileUpload = (event) => {
  const target = event.target;
  const file = target.files?.[0];
  
  if (file) {
    if (file.size > 10 * 1024 * 1024) {
      toast.warning('File size must be less than 10MB');
      target.value = '';
      return;
    }
    
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/jpg',
      'image/png'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      toast.warning('Please upload a valid document (PDF, DOC, DOCX, JPG, or PNG)');
      target.value = '';
      return;
    }
    
    formData.businessDocument = file;
    toast.success('Document uploaded successfully!');
  }
};

const detectLocation = async () => {
  if (!navigator.geolocation) {
    toast.error('Geolocation is not supported by your browser');
    return;
  }

  isDetectingLocation.value = true;
  toast.info('Detecting your location...');

  try {
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        timeout: 8000,
        maximumAge: 60000,
      });
    });

    const { latitude, longitude } = position.coords;

    const response = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&addressdetails=1`,
      { headers: { 'Accept-Language': 'en' } }
    );

    if (!response.ok) throw new Error('Geocoding failed');

    const data = await response.json();
    const addr = data.address;

    formData.address = `${addr.road || addr.suburb || addr.neighbourhood || ''} ${addr.house_number || ''}`.trim();
    formData.city = addr.city || addr.town || addr.village || addr.county || '';
    formData.state = addr.state || addr.region || '';
    formData.zipCode = addr.postcode || '';
    formData.country = addr.country || '';

    toast.success('Location detected! Please verify the details.');
  } catch (error) {
    console.error('Location detection error:', error);
    if (error.code === 1) {
      toast.error('Location access denied. Please allow location permission in your browser.');
    } else {
      // Demo fallback — fill with sample address for testing
      formData.address = '12 MG Road';
      formData.city = 'Bengaluru';
      formData.state = 'Karnataka';
      formData.zipCode = '560001';
      formData.country = 'India';
      toast.warning('Could not get live location. Demo address filled — please update if needed.');
    }
  } finally {
    isDetectingLocation.value = false;
  }
};

const handleNext = async () => {
  // Step 1 validation: Must select a role
  if (currentStep.value === 1) {
    if (!formData.role) {
      toast.warning('Please select a role (Customer or Vendor)');
      return;
    }
    currentStep.value++;
    return;
  }
  
  // Step 2 validation: Basic Info
  if (currentStep.value === 2) {
    if (!formData.firstName.trim()) {
      toast.warning('Please enter your first name');
      return;
    }
    if (!formData.lastName.trim()) {
      toast.warning('Please enter your last name');
      return;
    }
    if (!formData.email.trim()) {
      toast.warning('Please enter your email address');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast.warning('Please enter a valid email address');
      return;
    }
    if (!formData.phone.trim()) {
      toast.warning('Please enter your phone number');
      return;
    }
    if (!formData.password) {
      toast.warning('Please enter a password');
      return;
    }
    if (formData.password.length < 8) {
      toast.warning('Password must be at least 8 characters long');
      return;
    }
    if (!formData.confirmPassword) {
      toast.warning('Please confirm your password');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    // For Customers: Skip step 3 (Business Details) - go from 2 → 4
    if (formData.role === 'customer') {
      currentStep.value = 4;
      return;
    }
    
    currentStep.value++;
    return;
  }
  
  // Step 3 validation: Business Details (Vendors only)
  if (currentStep.value === 3) {
    if (formData.role === 'vendor') {
      if (!formData.companyName.trim()) {
        toast.warning('Please enter your company name');
        return;
      }
      if (formData.services.length === 0) {
        toast.warning('Please select at least one service you offer');
        return;
      }
      if (!formData.businessDocument) {
        toast.warning('Please upload a business verification document');
        return;
      }
    }
    currentStep.value++;
    return;
  }
  
  // Step 4 validation: Address
  if (currentStep.value === 4) {
    if (!formData.address.trim()) {
      toast.warning('Please enter your street address');
      return;
    }
    if (!formData.city.trim()) {
      toast.warning('Please enter your city');
      return;
    }
    if (!formData.state.trim()) {
      toast.warning('Please enter your state');
      return;
    }
    if (!formData.zipCode.trim()) {
      toast.warning('Please enter your ZIP code');
      return;
    }
    if (!formData.country.trim()) {
      toast.warning('Please enter your country');
      return;
    }

    isLoading.value = true;
    authStore.clearErrors();

    const result = await authStore.signup({
      role: formData.role,
      firstName: formData.firstName,
      lastName: formData.lastName,
      email: formData.email,
      phone: formData.phone,
      password: formData.password,
      company: formData.companyName || undefined,
      address: [formData.address, formData.city, formData.state, formData.zipCode, formData.country].filter(Boolean).join(', '),
    });

    isLoading.value = false;

    if (!result.success) {
      toast.error(result.message);
      return;
    }

    isSignupPrepared.value = true;
    currentStep.value++;
    return;
  }
  
  // Step 5: OTP has already been requested, continue to verification
  if (currentStep.value === 5) {
    if (!isSignupPrepared.value) {
      toast.error('Please complete signup details before verifying your email.');
      return;
    }

    sessionStorage.setItem('authFlow', 'signup');
    router.push({ path: '/2fa', query: { flow: 'signup' } });
  }
};

const handleBack = () => {
  if (currentStep.value === 5) {
    isSignupPrepared.value = false;
  }

  // For Customers: Skip step 3 (Business Details) - go from 4 → 2
  if (formData.role === 'customer' && currentStep.value === 4) {
    currentStep.value = 2;
    return;
  }
  
  if (currentStep.value > 1) {
    currentStep.value--;
  } else {
    goToSignIn();
  }
};
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
