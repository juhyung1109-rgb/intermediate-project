/* ==========================================================================
   SEMI-GUARD: Firebase Authentication & Firestore Integration Module
   Project: iceu-songpa03
   Features: Email/Password Sign-Up, Sign-In, Role Assignment, Auth State Observer
   ========================================================================== */

const firebaseConfig = {
  apiKey: "AIzaSyDyjdSJIzfBFYIZeoLV_L4ICWNBUeDT6cU",
  authDomain: "iceu-songpa03.firebaseapp.com",
  databaseURL: "https://iceu-songpa03-default-rtdb.firebaseio.com",
  projectId: "iceu-songpa03",
  storageBucket: "iceu-songpa03.firebasestorage.app",
  messagingSenderId: "94943462326",
  appId: "1:94943462326:web:e9b83fd642131479243717",
  measurementId: "G-D1595VRDL6"
};

let firebaseApp = null;
let firebaseAuth = null;
let firestoreDb = null;

try {
  if (typeof firebase !== 'undefined') {
    firebaseApp = firebase.initializeApp(firebaseConfig);
    firebaseAuth = firebase.auth();
    firestoreDb = firebase.firestore();
    console.log("🔥 Firebase Auth & Firestore successfully connected to iceu-songpa03!");
  } else {
    console.warn("Firebase SDK script not loaded yet.");
  }
} catch (err) {
  console.warn("Firebase Init note:", err);
}

// User Profile Cache
function getUserRole(uid, fallbackRole = 'engineer') {
  const cached = localStorage.getItem(`semiguard_role_${uid}`);
  return cached || fallbackRole;
}

function getUserName(uid, fallbackName = '') {
  const cached = localStorage.getItem(`semiguard_name_${uid}`);
  return cached || fallbackName;
}

// Multi-Channel Sync to Firestore named database 'project' (Collection: users)
async function syncUserToProjectFirestore(uid, role, name, email) {
  const finalName = name || (email ? email.split('@')[0] : '사용자');
  const targetRole = role || 'engineer';
  
  console.log(`📡 [Firestore Sync] Syncing user ${uid} (${finalName}) to database 'project'...`);

  // 1. Server-Side Sync via Cloud Run API (Uses Google Project IAM permissions)
  try {
    fetch('/api/sync-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uid: uid,
        email: email || '',
        name: finalName,
        displayName: finalName,
        role: targetRole
      })
    }).then(r => r.json()).then(res => {
      console.log("✅ [Cloud Run Sync] Wrote user to 'project' database:", res);
    }).catch(e => console.warn("[Cloud Run Sync] notice:", e));
  } catch (e) {}

  // 2. Client-Side Direct REST Sync with Firebase User Token
  try {
    if (firebaseAuth && firebaseAuth.currentUser) {
      const idToken = await firebaseAuth.currentUser.getIdToken();
      const url = `https://firestore.googleapis.com/v1/projects/iceu-songpa03/databases/project/documents/users/${uid}`;
      const payload = {
        fields: {
          email: { stringValue: email || '' },
          name: { stringValue: finalName },
          displayName: { stringValue: finalName },
          role: { stringValue: targetRole },
          updatedAt: { timestampValue: new Date().toISOString() }
        }
      };
      fetch(url, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      }).then(r => r.json()).then(res => {
        console.log("🔥 [Client REST Sync] Direct write to 'project' collection 'users' succeeded:", res);
      }).catch(err => console.warn("[Client REST Sync] notice:", err));
    }
  } catch (e) {
    console.warn("[Client REST Sync] error:", e);
  }

  // 3. Fallback write to default compat Firestore if initialized
  if (firestoreDb && uid) {
    firestoreDb.collection('users').doc(uid).set({
      role: targetRole,
      displayName: finalName,
      name: finalName,
      email: email || '',
      updatedAt: firebase.firestore.FieldValue.serverTimestamp()
    }, { merge: true }).catch(err => console.log('Firestore default instance note:', err));
  }
}

function setUserProfile(uid, role, name, email) {
  if (role) localStorage.setItem(`semiguard_role_${uid}`, role);
  if (name) localStorage.setItem(`semiguard_name_${uid}`, name);
  if (email && name) localStorage.setItem(`semiguard_name_${email}`, name);
  if (email && role) localStorage.setItem(`semiguard_role_${email}`, role);
  
  syncUserToProjectFirestore(uid, role, name, email);
}

// Backward compatibility alias
function setUserRole(uid, role) {
  setUserProfile(uid, role, null, null);
}

// Sign Up with Firebase
async function handleFirebaseSignUp(email, password, role, displayName) {
  if (!firebaseAuth) {
    throw new Error("Firebase SDK가 로드되지 않았습니다.");
  }
  const userCredential = await firebaseAuth.createUserWithEmailAndPassword(email, password);
  const user = userCredential.user;
  const finalName = displayName || email.split('@')[0];
  
  if (finalName && user.updateProfile) {
    try {
      await user.updateProfile({ displayName: finalName });
    } catch(e) {
      console.warn("User updateProfile notice:", e);
    }
  }
  
  setUserProfile(user.uid, role, finalName, email);
  await syncUserToProjectFirestore(user.uid, role, finalName, email);
  return { user, role, displayName: finalName };
}

// Sign In with Firebase
async function handleFirebaseSignIn(email, password, roleHint) {
  if (!firebaseAuth) {
    throw new Error("Firebase SDK가 로드되지 않았습니다.");
  }
  const userCredential = await firebaseAuth.signInWithEmailAndPassword(email, password);
  const user = userCredential.user;
  let role = getUserRole(user.uid, roleHint || 'engineer');
  let displayName = user.displayName || getUserName(user.uid) || localStorage.getItem(`semiguard_name_${email}`) || email.split('@')[0];
  
  // Try fetching profile from named database 'project' via REST
  try {
    const idToken = await user.getIdToken();
    const res = await fetch(`https://firestore.googleapis.com/v1/projects/iceu-songpa03/databases/project/documents/users/${user.uid}`, {
      headers: { 'Authorization': `Bearer ${idToken}` }
    });
    if (res.ok) {
      const docData = await res.json();
      if (docData.fields) {
        if (docData.fields.role?.stringValue) role = docData.fields.role.stringValue;
        if (docData.fields.displayName?.stringValue) displayName = docData.fields.displayName.stringValue;
        else if (docData.fields.name?.stringValue) displayName = docData.fields.name.stringValue;
      }
    }
  } catch (e) {
    console.log("REST read from 'project' fallback");
  }

  // Update profile in local cache and sync back to 'project'
  setUserProfile(user.uid, role, displayName, email);
  return { user, role, displayName };
}

// Sign Out with Firebase
async function handleFirebaseSignOut() {
  if (firebaseAuth) {
    await firebaseAuth.signOut();
  }
}

// Register Auth State Observer
function setupFirebaseAuthObserver(onUserChange) {
  if (!firebaseAuth) return;
  
  firebaseAuth.onAuthStateChanged(async (user) => {
    if (user) {
      if (user.email) localStorage.setItem('semiguard_current_email', user.email);
      let role = getUserRole(user.uid, 'engineer');
      let displayName = user.displayName || getUserName(user.uid) || localStorage.getItem(`semiguard_name_${user.email}`) || user.email.split('@')[0];
      try {
        const idToken = await user.getIdToken();
        const res = await fetch(`https://firestore.googleapis.com/v1/projects/iceu-songpa03/databases/project/documents/users/${user.uid}`, {
          headers: { 'Authorization': `Bearer ${idToken}` }
        });
        if (res.ok) {
          const docData = await res.json();
          if (docData.fields) {
            if (docData.fields.role?.stringValue) role = docData.fields.role.stringValue;
            if (docData.fields.displayName?.stringValue) displayName = docData.fields.displayName.stringValue;
            else if (docData.fields.name?.stringValue) displayName = docData.fields.name.stringValue;
          }
        }
      } catch (e) {}
      onUserChange({
        isLoggedIn: true,
        uid: user.uid,
        email: user.email,
        name: displayName,
        role: role
      });
    } else {
      onUserChange({
        isLoggedIn: false,
        uid: null,
        email: null,
        role: 'engineer'
      });
    }
  });
}
