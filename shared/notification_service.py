import twilio from 'twilio';
import nodemailer from 'nodemailer';
import admin from 'firebase-admin';
import express from 'express';

// Initialize Twilio
const twilioClient = twilio('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN');
// Initialize Firebase Admin
admin.initializeApp();

const app = express();
app.use(express.json());

// Send SMS via Twilio
const sendSms = (to, message) => {
    return twilioClient.messages.create({
        to: to,
        from: 'YOUR_TWILIO_NUMBER',
        body: message,
    });
};

// Send Email Notifications
const sendEmail = async (to, subject, text) => {
    let transporter = nodemailer.createTransport({
        service: 'gmail',
        auth: {
            user: 'YOUR_EMAIL@gmail.com',
            pass: 'YOUR_EMAIL_PASSWORD',
        },
    });

    let mailOptions = {
        from: 'YOUR_EMAIL@gmail.com',
        to: to,
        subject: subject,
        text: text,
    };

    return transporter.sendMail(mailOptions);
};

// Send Push Notifications via Firebase
const sendPushNotification = (token, payload) => {
    return admin.messaging().send({
        token: token,
        notification: payload,
    });
};

// Real-time Alerts in App
const sendRealTimeAlert = (req, res) => {
    // Emit alert using your preferred method (e.g., WebSocket, server-sent events)
    res.send('Real-time alert triggered!');
};

app.post('/notify', (req, res) => {
    const { smsTo, emailTo, pushToken, alertMessage } = req.body;
    const promises = [];

    if (smsTo) {
        promises.push(sendSms(smsTo, alertMessage));
    }

    if (emailTo) {
        promises.push(sendEmail(emailTo, 'Notification', alertMessage));
    }

    if (pushToken) {
        promises.push(sendPushNotification(pushToken, { title: 'Notification', body: alertMessage }));
    }

    Promise.all(promises)
        .then(() => res.status(200).send('Notifications sent.'))
        .catch(err => res.status(500).send('Error sending notifications: ' + err.message));
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
