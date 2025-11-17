// Test Supabase Real-time Connection
// Run this in your browser console on http://localhost:3000

import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  'https://kuxwmlxghamrslgbxiof.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt1eHdtbHhnaGFtcnNsZ2J4aW9mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMyMTU4NjcsImV4cCI6MjA3ODc5MTg2N30.LF2VtyFhC_gAqj0jJyBE5bcfYmPcIHOt5kmJCO0wETc'
);

console.log('🔌 Testing Supabase real-time connection...');

const channel = supabase
  .channel('test-channel')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'repo-updates',
    },
    (payload) => {
      console.log('✅ Received update:', payload);
    }
  )
  .subscribe((status) => {
    console.log('📡 Subscription status:', status);
  });

console.log('✨ Listening for changes on repo-updates table...');
console.log('💡 Now run your backend and watch for updates here!');
